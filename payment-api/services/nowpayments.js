const axios = require("axios");
const crypto = require("crypto");

class NowPaymentsService {
  constructor() {
    this.apiKey = process.env.NOWPAYMENTS_API_KEY;
    this.ipnSecret = process.env.NOWPAYMENTS_IPN_SECRET;
    this.apiUrl = "https://api.nowpayments.io/v1";
  }

  async createPayment(tx_id, amount, currency = "USD") {
    try {
      const response = await axios.post(
        `${this.apiUrl}/invoice`,
        {
          price_amount: amount,
          price_currency: currency,
          pay_currency: "btc,eth,usdt,ltc,trx",
          order_id: tx_id,
          order_description: `Vexa Bot Shop - Payment ${tx_id}`,
          ipn_callback_url: `${process.env.SERVER_URL || "http://localhost:3001"}/api/payments/nowpayments/ipn`,
          success_url: "https://discord.com/channels/@me",
          cancel_url: "https://discord.com/channels/@me",
        },
        {
          headers: {
            "x-api-key": this.apiKey,
            "Content-Type": "application/json",
          },
        }
      );

      return {
        payment_id: response.data.id,
        invoice_url: response.data.invoice_url,
        payment_status: response.data.payment_status,
      };
    } catch (error) {
      throw new Error(`NowPayments error: ${error.message}`);
    }
  }

  verifyIPNSignature(body, signature) {
    if (!this.ipnSecret) return true;
    const computed = crypto
      .createHmac("sha512", this.ipnSecret)
      .update(JSON.stringify(body))
      .digest("hex");
    return computed === signature;
  }
}

module.exports = new NowPaymentsService();
