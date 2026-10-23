from flask import Flask, request, render_template_string
import matplotlib
matplotlib.use("Agg")  # Draw charts without opening a window
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #090d16; color: #f8fafc; }
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(56, 189, 248, 0.15);
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .neon-glow { box-shadow: 0 0 20px rgba(56, 189, 248, 0.4); }
        .neon-glow:hover { box-shadow: 0 0 30px rgba(56, 189, 248, 0.7); }
        input { background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 0.75rem;
                padding: 0.6rem 1rem; width: 100%; font-size: 0.875rem; color: #f1f5f9; outline: none; }
        input:focus { border-color: #22d3ee; box-shadow: 0 0 0 1px #22d3ee; }
        label { display: block; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em;
                color: #22d3ee; text-transform: uppercase; margin-bottom: 0.3rem; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <div class="w-full max-w-4xl mx-auto space-y-6">

        <!-- Header -->
        <div class="text-center">
            <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                Health Report
            </h1>
            <p class="text-slate-400 text-sm mt-2">Enter your details to see your stats next to the ideal values</p>
        </div>

        <!-- Form card -->
        <div class="glass-card rounded-3xl p-6 md:p-8 relative overflow-hidden">
            <div class="absolute -top-32 -left-32 w-72 h-72 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none"></div>
            <div class="absolute -bottom-32 -right-32 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

            <form method="POST" id="healthForm" class="relative z-10">
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-5 gap-y-4">
                    <div>
                        <label>Name</label>
                        <input type="text" name="name" value="{{ form.name }}" required>
                    </div>
                    <div>
                        <label>Age</label>
                        <input type="number" name="age" value="{{ form.age }}" required>
                    </div>
                    <div>
                        <label>Weight (kg)</label>
                        <input type="number" step="any" name="weight" value="{{ form.weight }}" required>
                    </div>
                    <div>
                        <label>Height (cm)</label>
                        <input type="number" step="any" name="height" value="{{ form.height }}" required>
                    </div>
                    <div>
                        <label>Heart rate (bpm)</label>
                        <input type="number" step="any" name="heart" value="{{ form.heart }}" required>
                    </div>
                    <div>
                        <label>Sleep (hours per night)</label>
                        <input type="number" step="any" name="sleep" value="{{ form.sleep }}" required>
                    </div>
                </div>

                {% if error %}
                    <p class="text-red-400 text-sm mt-4">{{ error }}</p>
                {% endif %}

                <div class="flex flex-col-reverse sm:flex-row sm:justify-between gap-3 mt-6">
                    <!-- Clear: reloads the page with no data, so the form AND the chart are emptied -->
                    <button type="button" onclick="window.location.href = window.location.pathname;"
                            class="py-3.5 px-8 rounded-xl border border-slate-600 text-slate-300 font-semibold text-sm tracking-wide
                                   hover:border-cyan-400 hover:text-cyan-300 transition-all duration-300 transform active:scale-95">
                        Clear
                    </button>

                    <button type="submit"
                            class="py-3.5 px-10 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold text-sm tracking-wide neon-glow transition-all duration-300 transform active:scale-95">
                        Show Report
                    </button>
                </div>
            </form>
        </div>

        <!-- Chart card -->
        <div class="glass-card rounded-3xl p-6 md:p-8">
            <h2 class="text-xs font-semibold tracking-widest text-cyan-400 uppercase mb-4">Your Report</h2>
            <div class="flex items-center justify-center bg-slate-950/50 border border-slate-800/80 rounded-2xl p-4 min-h-[260px]">
                {% if plot_url %}
                    <img src="data:image/png;base64,{{ plot_url }}" alt="Health Report Chart" class="w-full h-auto rounded-lg">
                {% else %}
                    <p class="text-sm text-slate-500">Fill in the form to see your report</p>
                {% endif %}
            </div>
        </div>

    </div>

</body>
</html>
"""


def make_chart(name, age, bmi, heart, sleep):
    labels = ["BMI", "Heart Rate (bpm)", "Sleep (hours)"]
    values = [bmi, heart, sleep]      # patient (changes)
    ideal = [21.7, 80, 8]             # standard (always fixed)

    fig, axes = plt.subplots(1, 3, figsize=(9, 3.8), dpi=110)
    fig.patch.set_facecolor("#0f172a")

    for i in range(3):
        ax = axes[i]
        ax.set_facecolor("#0f172a")
        ax.bar(["Ideal", "Patient"], [ideal[i], values[i]], color=["#22c55e", "#ef4444"])
        ax.set_ylim(0, max(ideal[i], values[i]) * 1.25)   # room for the numbers on top
        ax.set_title(labels[i], color="#f8fafc", fontsize=10, fontweight="bold")
        ax.tick_params(colors="#94a3b8", labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.text(0, ideal[i], str(ideal[i]), ha="center", va="bottom", color="#f8fafc", fontsize=9)
        ax.text(1, values[i], str(values[i]), ha="center", va="bottom", color="#f8fafc", fontsize=9)

    fig.suptitle(f"Health Report - {name} (Age {age})", color="#f8fafc", fontsize=12, fontweight="bold")
    fig.tight_layout()

    img = io.BytesIO()
    fig.savefig(img, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()


@app.route("/", methods=["GET", "POST"])
def index():
    plot_url = None
    error = None
    form = {"name": "", "age": "", "weight": "", "height": "", "heart": "", "sleep": ""}

    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        try:
            name = form["name"]
            age = int(form["age"])
            weight = float(form["weight"])
            height = float(form["height"]) / 100   # cm -> metres
            heart = float(form["heart"])
            sleep = float(form["sleep"])
            bmi = round(weight / (height * height), 1)
        except (ValueError, ZeroDivisionError):
            error = "Please fill all boxes with valid numbers (height cannot be 0)."
        else:
            plot_url = make_chart(name, age, bmi, heart, sleep)

    return render_template_string(HTML_TEMPLATE, plot_url=plot_url, error=error, form=form)


if __name__ == "__main__":
    app.run(debug=True)