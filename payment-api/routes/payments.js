const express = require("express");
const router = express.Router();
const mongoose = require("mongoose");
const zarinpal = require("../services/zarinpal");
const nowpayments = require("../services/nowpayments");

const transactionSchema = new mongoose.Schema({
  tx_id: { type: String, unique: true, required: true },
  user_id: { type: Number, required: true },
  product_id: { type: String, required: true },
  amount: { type: Number, required: true },
  currency: { type: String, default: "USD" },
  gateway: { type: String, enum: ["zarinpal", "nowpayments"], required: true },
  status: { type: String, enum: ["pending", "completed", "failed"], default: "pending" },
  gateway_tx_id: { type: String },
  payment_url: { type: String },
  referrer_id: { type: Number, default: null },
  referral_bonus: { type: Number, default: 0 },
  created_at: { type: Date, default: Date.now },
  completed_at: { type: Date },
});

const Transaction = mongoose.model("PaymentTransaction", transactionSchema);

// Create payment
router.post("/create", async (req, res) => {
  try {
    const { tx_id, user_id, product_id, amount, currency, gateway, callback_url } = req.body;

    if (!tx_id || !user_id || !product_id || !amount || !gateway) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    let paymentResult;

    if (gateway === "zarinpal") {
      paymentResult = await zarinpal.createPayment(tx_id, amount, currency || "IRR");
    } else if (gateway === "nowpayments") {
      paymentResult = await nowpayments.createPayment(tx_id, amount, currency || "USD");
    } else {
      return res.status(400).json({ error: `Unsupported gateway: ${gateway}` });
    }

    await Transaction.create({
      tx_id,
      user_id,
      product_id,
      amount,
      currency: currency || (gateway === "zarinpal" ? "IRR" : "USD"),
      gateway,
      payment_url: paymentResult.pay_link || paymentResult.invoice_url,
      gateway_tx_id: paymentResult.authority || paymentResult.payment_id?.toString(),
    });

    res.json({
      success: true,
      tx_id,
      payment_url: paymentResult.pay_link || paymentResult.invoice_url,
      gateway,
    });
  } catch (error) {
    console.error("Payment creation error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Verify ZarinPal
router.get("/zarinpal/verify", async (req, res) => {
  try {
    const { Authority, Status } = req.query;
    if (Status !== "OK") {
      return res.redirect("https://discord.com/channels/@me?payment=failed");
    }

    const tx = await Transaction.findOne({ gateway_tx_id: Authority });
    if (!tx) {
      return res.redirect("https://discord.com/channels/@me?payment=notfound");
    }

    const verification = await zarinpal.verifyPayment(Authority, tx.amount);
    if (verification.code === 100) {
      tx.status = "completed";
      tx.completed_at = new Date();
      await tx.save();
      return res.redirect(`https://discord.com/channels/@me?payment=success&tx=${tx.tx_id}`);
    }

    res.redirect("https://discord.com/channels/@me?payment=failed");
  } catch (error) {
    res.redirect("https://discord.com/channels/@me?payment=error");
  }
});

// NowPayments IPN
router.post("/nowpayments/ipn", async (req, res) => {
  try {
    const signature = req.headers["x-nowpayments-sig"];
    if (!nowpayments.verifyIPNSignature(req.body, signature)) {
      return res.status(401).json({ error: "Invalid signature" });
    }

    if (req.body.payment_status === "finished") {
      const tx = await Transaction.findOne({ gateway_tx_id: req.body.payment_id?.toString() });
      if (tx && tx.status !== "completed") {
        tx.status = "completed";
        tx.completed_at = new Date();
        await tx.save();
      }
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get payment status
router.get("/status/:tx_id", async (req, res) => {
  try {
    const tx = await Transaction.findOne({ tx_id: req.params.tx_id });
    if (!tx) return res.status(404).json({ error: "Transaction not found" });
    res.json(tx);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
