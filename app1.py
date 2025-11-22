from flask import Flask, render_template, request, send_file
import os
from io import BytesIO
from weasyprint import HTML
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        try:
            carat = float(request.form.get("carat", 0))
            gold_rate = float(request.form.get("rate", 0))
            weight = float(request.form.get("weight", 0))
            jewelry_type = request.form.get("type", "Ring")

            # ✅ Default values from ConfigMap
            default_making = float(os.getenv(f"DEFAULT_MAKING_{jewelry_type.upper()}"))
            default_wastage = float(os.getenv(f"DEFAULT_WASTAGE_{jewelry_type.upper()}",))
            gst_gold = float(os.getenv("DEFAULT_GST_GOLD", "3.0"))
            gst_making = float(os.getenv("DEFAULT_GST_MAKING", "5.0"))

            # ✅ Use user input or fallback to default
            making_charge = float(request.form.get("making") or default_making)
            wastage = float(request.form.get("wastage") or default_wastage)

            # --- Calculations ---
            purity = carat / 24
            pure_gold_price = gold_rate * purity
            base_cost = pure_gold_price * weight
            wastage_charge = (wastage / 100) * base_cost
            making_charge_amt = (making_charge / 100) * base_cost
            subtotal = base_cost + wastage_charge + making_charge_amt

            gst_gold_amt = (gst_gold / 100) * base_cost
            gst_making_amt = (gst_making / 100) * making_charge_amt
            total_gst = gst_gold_amt + gst_making_amt
            total_price = subtotal + total_gst

            result = {
                "jewelry_type": jewelry_type,
                "gold_rate": gold_rate,
                "carat": carat,
                "purity": round(purity * 100, 2),
                "weight": weight,
                "base_cost": round(base_cost, 2),
                "wastage_charge": round(wastage_charge, 2),
                "making_charge_amt": round(making_charge_amt, 2),
                "subtotal": round(subtotal, 2),
                "gst_gold_amt": round(gst_gold_amt, 2),
                "gst_making_amt": round(gst_making_amt, 2),
                "total_gst": round(total_gst, 2),
                "total_price": round(total_price, 2),
                "making_charge": making_charge,
                "wastage": wastage
            }

        except ValueError:
            result = "Invalid input. Please enter valid numbers."

    return render_template("index.html", result=result)

@app.route("/receipt")
def receipt():
    result = request.args.to_dict()
    result['timestamp'] = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    html = render_template("receipt.html", result=result)
    pdf_bytes = HTML(string=html).write_pdf()
    return send_file(BytesIO(pdf_bytes),
                     as_attachment=True,
                     download_name="Jewellery_Receipt.pdf",
                     mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


# from flask import Flask, render_template, request, send_file
# import os
# from io import BytesIO
# from weasyprint import HTML

# app = Flask(__name__)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     result = ""
#     if request.method == "POST":
#         try:
#             number_fields = ["carat", "rate", "weight", "making", "wastage"]
#             for field in number_fields:
#                 value = request.form[field]
#                 try:
#                     float(value)
#                 except ValueError:
#                     raise ValueError(f"{field} must be a number.")

#             carat = float(request.form["carat"])
#             gold_rate = float(request.form["rate"])
#             weight = float(request.form["weight"])
#             making_charge = float(request.form["making"])
#             wastage = float(request.form["wastage"])

#             gst_gold = float(os.getenv("DEFAULT_GST_GOLD", "3.0"))
#             gst_making = float(os.getenv("DEFAULT_GST_MAKING", "5.0"))

#             purity = carat / 24
#             pure_gold_price = gold_rate * purity
#             base_cost = pure_gold_price * weight
#             wastage_charge = (wastage / 100) * base_cost
#             making_charge_amt = (making_charge / 100) * base_cost
#             subtotal = base_cost + wastage_charge + making_charge_amt

#             gst_gold_amt = (gst_gold / 100) * base_cost
#             gst_making_amt = (gst_making / 100) * making_charge_amt
#             total_gst = gst_gold_amt + gst_making_amt
#             total_price = subtotal + total_gst

#             result = {
#                 "gold_rate": gold_rate,
#                 "carat": carat,
#                 "purity": round(purity * 100, 2),
#                 "weight": weight,
#                 "base_cost": round(base_cost, 2),
#                 "wastage_charge": round(wastage_charge, 2),
#                 "making_charge_amt": round(making_charge_amt, 2),
#                 "subtotal": round(subtotal, 2),
#                 "gst_gold_amt": round(gst_gold_amt, 2),
#                 "gst_making_amt": round(gst_making_amt, 2),
#                 "total_gst": round(total_gst, 2),
#                 "total_price": round(total_price, 2)
#             }
#         except ValueError:
#             result = "Invalid input. Please enter valid numbers."

#     return render_template("index.html", result=result)

# @app.route("/receipt")
# def receipt():
#     result = request.args.to_dict()
#     html = render_template("receipt.html", result=result)
#     pdf = BytesIO()
#     HTML(string=html).write_pdf(pdf)
#     pdf.seek(0)
#     return send_file(pdf, as_attachment=True, download_name="Jewellery_Receipt.pdf", mimetype="application/pdf")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)