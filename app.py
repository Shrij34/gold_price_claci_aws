# /mnt/data/app.py
from flask import Flask, render_template, request, send_file, jsonify
import os
from io import BytesIO
from weasyprint import HTML
from datetime import datetime
import logging
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# ---------------- Prometheus metrics ----------------
REQUEST_COUNT = Counter(
    "goldcalc_requests_total",
    "Total HTTP requests to goldcalc",
    ['endpoint', 'method', 'status']
)
REQUEST_LATENCY = Histogram(
    "goldcalc_request_latency_seconds",
    "Request latency in seconds",
    ['endpoint']
)

# ---------------- Logging (structured) ----------------
logger = logging.getLogger("goldcalc")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(os.getenv("GOLDCALC_LOG_LEVEL", "INFO"))

# ---------------- Helpers ----------------
def instrument(endpoint):
    """decorator-like wrapper for simple instrumentation in routes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                resp = func(*args, **kwargs)
                status_code = resp[1] if isinstance(resp, tuple) and len(resp) > 1 else 200
                REQUEST_COUNT.labels(endpoint=endpoint, method=request.method, status=str(status_code)).inc()
                return resp
            except Exception as e:
                REQUEST_COUNT.labels(endpoint=endpoint, method=request.method, status="500").inc()
                logger.exception(f"exception in {endpoint}: {e}")
                raise
            finally:
                REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# ---------------- Routes ----------------
@app.route("/", methods=["GET", "POST"])
@instrument("/")
def index():
    result = ""
    if request.method == "POST":
        try:
            carat = float(request.form.get("carat", 0))
            gold_rate = float(request.form.get("rate", 0))
            weight = float(request.form.get("weight", 0))
            jewelry_type = request.form.get("type", "Ring")

            # ConfigMap-driven defaults (safe fallback)
            default_making = float(os.getenv(f"DEFAULT_MAKING_{jewelry_type.upper()}", "20"))
            default_wastage = float(os.getenv(f"DEFAULT_WASTAGE_{jewelry_type.upper()}", "10"))
            gst_gold = float(os.getenv("DEFAULT_GST_GOLD", "3.0"))
            gst_making = float(os.getenv("DEFAULT_GST_MAKING", "5.0"))

            making_charge = float(request.form.get("making") or default_making)
            wastage = float(request.form.get("wastage") or default_wastage)

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

            logger.info(f"calculation success type={jewelry_type} base_cost={result['base_cost']} total={result['total_price']}")

            # render template will show result
        except ValueError as ve:
            logger.warning(f"bad input: {ve}")
            result = "Invalid input. Please enter valid numbers."
        except Exception as e:
            logger.exception(f"unexpected error: {e}")
            result = "An error occurred. Check logs."

    return render_template("index.html", result=result)

@app.route("/receipt")
@instrument("/receipt")
def receipt():
    result = request.args.to_dict()
    result['timestamp'] = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    html = render_template("receipt.html", result=result)
    pdf_bytes = HTML(string=html).write_pdf()
    logger.info(f"receipt generated for {result.get('jewelry_type','-')} total={result.get('total_price','-')}")
    return send_file(BytesIO(pdf_bytes),
                     as_attachment=True,
                     download_name="Jewellery_Receipt.pdf",
                     mimetype="application/pdf")

@app.route("/health")
def health():
    # simple health check used by k8s liveness/readiness
    return jsonify({"status": "ok"}), 200

@app.route("/metrics")
def metrics():
    # Expose Prometheus metrics
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
