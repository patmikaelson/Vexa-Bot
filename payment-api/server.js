const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const mongoose = require("mongoose");
const Redis = require("ioredis");
const crypto = require("crypto");
const axios = require("axios");

const app = express();
const PORT = process.env.PORT || 3001;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://admin:vexasecure2024@localhost:27017/vexa?authSource=admin";
const REDIS_URL = process.env.REDIS_URL || "redis://:vexaredis2024@localhost:6379/0";
const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL || "";

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// MongoDB Connection
mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
}).then(() => console.log("✅ Payment API connected to MongoDB"))
  .catch(err => console.error("❌ MongoDB connection error:", err));

// Redis Connection
const redis = new Redis(REDIS_URL, {
  retryStrategy: (times) => Math.min(times * 50, 2000),
});

// Mongoose Schemas
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

const Transaction = mongoose.model("Transaction", transactionSchema);

// ==================== PAYMENT ROUTES ====================

// Bot-facing: create payment
app.post("/create-payment", async (req, res) => {
  try {
    const { tx_id, user_id, product_id, amount, currency, gateway, callback_url } = req.body;

    if (!tx_id || !user_id || !product_id || !amount || !gateway) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    let paymentResult;

    if (gateway === "zarinpal") {
      paymentResult = await createZarinPalPayment(tx_id, amount, currency || "IRR", callback_url);
    } else if (gateway === "nowpayments") {
      paymentResult = await createNowPaymentsPayment(tx_id, amount, currency || "USD", callback_url);
    } else {
      return res.status(400).json({ error: `Unsupported gateway: ${gateway}` });
    }

    // Store payment URL in transaction
    await Transaction.findOneAndUpdate(
      { tx_id },
      { payment_url: paymentResult.pay_link || paymentResult.payment_url }
    );

    // Cache in Redis
    await redis.setex(`payment:${tx_id}`, 3600, JSON.stringify({
      tx_id, user_id, product_id, amount, gateway, status: "pending"
    }));

    res.json({
      success: true,
      tx_id,
      payment_url: paymentResult.pay_link || paymentResult.payment_url,
      gateway,
    });
  } catch (error) {
    console.error("Payment creation error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Unified verify endpoint for both gateways
app.get("/verify-payment", async (req, res) => {
  const { gateway, authority, payment_id, Status } = req.query;
  if (gateway === "zarinpal" || (authority && Status)) {
    return handleZarinPalVerify(req, res);
  }
  res.status(400).json({ error: "Unsupported gateway or missing params" });
});

async function handleZarinPalVerify(req, res) {
  try {
    const { Authority, Status } = req.query;
    if (Status !== "OK") {
      return res.status(400).json({ error: "Payment cancelled or failed" });
    }

    const response = await axios.post("https://api.zarinpal.com/pg/v4/payment/verify.json", {
      merchant_id: process.env.ZARINPAL_MERCHANT_ID,
      authority: Authority,
      amount: 0,
    });

    if (response.data.data.code === 100) {
      const tx = await Transaction.findOne({ gateway_tx_id: Authority });
      if (tx) {
        await completePayment(tx.tx_id, Authority);
      }
      res.redirect(`https://discord.com/channels/@me?payment=success&tx=${tx?.tx_id || ""}`);
    } else {
      res.redirect("https://discord.com/channels/@me?payment=failed");
    }
  } catch (error) {
    console.error("ZarinPal verify error:", error);
    res.status(500).json({ error: error.message });
  }
}

app.get("/api/payments/zarinpal/verify", handleZarinPalVerify);

// NowPayments IPN Webhook
app.post("/api/payments/nowpayments/ipn", async (req, res) => {
  try {
    const body = req.body;
    const ipnSecret = process.env.NOWPAYMENTS_IPN_SECRET;

    // Verify IPN signature
    const receivedSignature = req.headers["x-nowpayments-sig"];
    if (ipnSecret) {
      const computedSignature = crypto
        .createHmac("sha512", ipnSecret)
        .update(JSON.stringify(body))
        .digest("hex");
      if (receivedSignature !== computedSignature) {
        return res.status(401).json({ error: "Invalid signature" });
      }
    }

    if (body.payment_status === "finished") {
      const tx = await Transaction.findOne({ gateway_tx_id: body.payment_id?.toString() });
      if (tx) {
        await completePayment(tx.tx_id, body.payment_id?.toString());
      }
    }

    res.json({ success: true });
  } catch (error) {
    console.error("NowPayments IPN error:", error);
    res.status(500).json({ error: error.message });
  }
});

// Check payment status
app.get("/api/payments/status/:tx_id", async (req, res) => {
  try {
    const cached = await redis.get(`payment:${req.params.tx_id}`);
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    const tx = await Transaction.findOne({ tx_id: req.params.tx_id });
    if (!tx) {
      return res.status(404).json({ error: "Transaction not found" });
    }

    res.json({
      tx_id: tx.tx_id,
      user_id: tx.user_id,
      product_id: tx.product_id,
      amount: tx.amount,
      gateway: tx.gateway,
      status: tx.status,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== PAYMENT GATEWAYS ====================

async function createZarinPalPayment(tx_id, amount, currency, callback_url) {
  const merchantID = process.env.ZARINPAL_MERCHANT_ID;
  if (!merchantID) {
    throw new Error("ZARINPAL_MERCHANT_ID not configured");
  }

  // Convert USD to IRR (approximate)
  const amountIRR = currency === "IRR"
    ? Math.round(amount)
    : Math.round(amount * 42000); // Approximate conversion

  const response = await axios.post("https://api.zarinpal.com/pg/v4/payment/request.json", {
    merchant_id: merchantID,
    amount: amountIRR,
    description: `Vexa Bot Shop - Transaction ${tx_id}`,
    callback_url: callback_url || `${process.env.ZARINPAL_CALLBACK_URL || "http://localhost:3001/api/payments/zarinpal/verify"}`,
    metadata: {
      tx_id,
      mobile: "",
      email: "",
    },
  });

  if (response.data.data.code === 100) {
    const authority = response.data.data.authority;
    // Store authority for verification
    await Transaction.findOneAndUpdate({ tx_id }, { gateway_tx_id: authority });

    return {
      pay_link: `https://www.zarinpal.com/pg/StartPay/${authority}`,
      authority,
    };
  }

  throw new Error(`ZarinPal error: ${response.data.errors?.message || "Unknown"}`);
}

async function createNowPaymentsPayment(tx_id, amount, currency, callback_url) {
  const apiKey = process.env.NOWPAYMENTS_API_KEY;
  if (!apiKey) {
    throw new Error("NOWPAYMENTS_API_KEY not configured");
  }

  const response = await axios.post(
    "https://api.nowpayments.io/v1/invoice",
    {
      price_amount: amount,
      price_currency: currency || "USD",
      pay_currency: "btc,eth,usdt,ltc",
      order_id: tx_id,
      order_description: `Vexa Bot Shop - Transaction ${tx_id}`,
      ipn_callback_url: `${process.env.SERVER_URL || "http://localhost:3001"}/api/payments/nowpayments/ipn`,
      success_url: callback_url || "https://discord.com/channels/@me",
      cancel_url: callback_url || "https://discord.com/channels/@me",
    },
    {
      headers: {
        "x-api-key": apiKey,
        "Content-Type": "application/json",
      },
    }
  );

  if (response.data && response.data.invoice_url) {
    const paymentId = response.data.id?.toString();
    if (paymentId) {
      await Transaction.findOneAndUpdate({ tx_id }, { gateway_tx_id: paymentId });
    }

    return {
      payment_url: response.data.invoice_url,
      payment_id: response.data.id,
    };
  }

  throw new Error(`NowPayments error: ${JSON.stringify(response.data)}`);
}

// ==================== COMPLETE PAYMENT ====================

async function completePayment(tx_id, gateway_tx_id) {
  const tx = await Transaction.findOne({ tx_id });
  if (!tx || tx.status === "completed") return;

  // Update transaction
  tx.status = "completed";
  tx.completed_at = new Date();
  tx.gateway_tx_id = gateway_tx_id || tx.gateway_tx_id;
  await tx.save();

  // Send notification to Discord
  if (DISCORD_WEBHOOK_URL) {
    try {
      await axios.post(DISCORD_WEBHOOK_URL, {
        embeds: [{
          title: "✅ Payment Completed",
          color: 0x00C853,
          fields: [
            { name: "🆔 TX ID", value: `\`${tx_id}\``, inline: true },
            { name: "👤 User", value: `<@${tx.user_id}>`, inline: true },
            { name: "🤖 Product", value: tx.product_id, inline: true },
            { name: "💰 Amount", value: `$${tx.amount.toFixed(2)}`, inline: true },
            { name: "💳 Gateway", value: tx.gateway, inline: true },
            { name: "📅 Date", value: `<t:${Math.floor(Date.now() / 1000)}:R>`, inline: true },
          ],
          footer: { text: "Vexa • Secure Bot Shop" },
          timestamp: new Date().toISOString(),
        }],
      });
    } catch (e) {
      console.error("Webhook error:", e.message);
    }
  }

  // Update cache
  await redis.setex(`payment:${tx_id}`, 3600, JSON.stringify({
    tx_id, user_id: tx.user_id, product_id: tx.product_id,
    amount: tx.amount, gateway: tx.gateway, status: "completed"
  }));
}

// ==================== START SERVER ====================

app.listen(PORT, () => {
  console.log(`💳 Payment API running on port ${PORT}`);
  console.log(`   MongoDB: ${MONGODB_URI}`);
  console.log(`   Redis: ${REDIS_URL}`);
});
