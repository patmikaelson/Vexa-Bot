const axios = require("axios");

class ZarinPalService {
  constructor() {
    this.merchantID = process.env.ZARINPAL_MERCHANT_ID;
    this.apiUrl = "https://api.zarinpal.com/pg/v4";
    this.callbackUrl = process.env.ZARINPAL_CALLBACK_URL || "http://localhost:3001/api/payments/zarinpal/verify";
  }

  async createPayment(tx_id, amount, currency = "IRR") {
    const amountIRR = currency === "IRR"
      ? Math.round(amount)
      : Math.round(amount * 42000);

    try {
      const response = await axios.post(`${this.apiUrl}/payment/request.json`, {
        merchant_id: this.merchantID,
        amount: amountIRR,
        description: `Vexa Bot Shop - Payment ${tx_id}`,
        callback_url: this.callbackUrl,
        metadata: { tx_id },
      });

      if (response.data.data.code === 100) {
        return {
          authority: response.data.data.authority,
          pay_link: `https://www.zarinpal.com/pg/StartPay/${response.data.data.authority}`,
        };
      }

      throw new Error(response.data.errors?.message || "ZarinPal error");
    } catch (error) {
      throw new Error(`ZarinPal payment error: ${error.message}`);
    }
  }

  async verifyPayment(authority, amount) {
    try {
      const response = await axios.post(`${this.apiUrl}/payment/verify.json`, {
        merchant_id: this.merchantID,
        authority,
        amount,
      });

      return response.data.data;
    } catch (error) {
      throw new Error(`ZarinPal verify error: ${error.message}`);
    }
  }
}

module.exports = new ZarinPalService();
