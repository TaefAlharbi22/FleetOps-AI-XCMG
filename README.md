# FleetOps AI — AI Operations Agent for Construction Equipment

مساعد ذكي (AI Agent) يحلل بيانات تشغيل معدات الإنشاء (ساعات التشغيل، التوقف، الوقود، الصيانة)
ويجيب على أسئلة المستخدم باللغة الطبيعية، ويقدّم Insights وتوصيات قابلة للتنفيذ عبر واجهة Streamlit.

مشروع مقدَّم لمسار **AI + Construction Machinery → AI + Operation**
في الدورة الـ15 من المسابقة الصينية الدولية للابتكار وريادة الأعمال.

## الحالة الحالية
- [x] Day 1-2: هيكل المشروع + بيانات أسطول واقعية (Synthetic Dataset)
- [x] Day 3: حساب مؤشرات الأداء (KPIs)
- [x] Day 4: بناء أدوات التحليل (Tool Functions) للـ AI Agent
- [x] Day 5: ربط LLM API + Agent Logic (Optional LLM Mode + Built-in AI Mode)
- [x] Day 6: واجهة Streamlit (Dashboard + Chat) — تم اختبارها محليًا وتعمل بنجاح
- [x] Day 7: كشف شذوذ بالـ Machine Learning (Isolation Forest) + Attention Score موحّد
- [x] Day 8: اختبار شامل (Edge Cases) — لا يوجد أي تعطل حتى مع أسئلة غامضة/فارغة
- [x] Day 9: تقرير المشروع (PDF) + العرض التقديمي (PPTX) + نوت بوك Colab
- [x] Day 10: المراجعة النهائية — كل الملفات جاهزة للتسليم

## هيكل المشروع
```
fleetops-ai/
├── data/               # البيانات (خام ومُعالجة)
│   ├── equipment_master.csv
│   ├── fleet_daily_logs.csv
│   ├── equipment_kpis.csv
│   └── weekly_utilization_by_project.csv
├── notebooks/          # تحليل واستكشاف (EDA)
├── src/                # كود المعالجة والتحليل
│   ├── generate_data.py
│   └── kpis.py
├── app/                # تطبيق Streamlit
├── reports/            # المخرجات والرسوم
├── presentation/       # الشرائح وفيديو العرض
├── requirements.txt
└── README.md
```

## البيانات
بيانات تشغيل يومية لـ 30 معدة (حفارات، لوادر، شاحنات قلابة، جرافات، رافعات، غريدر)
عبر 90 يومًا و 5 مشاريع إنشائية، تتضمن أنماطًا واقعية ومشاكل مقصودة لأغراض العرض:
- 3 معدات بمعدل Downtime مرتفع بشكل غير طبيعي
- معدة واحدة بارتفاع مفاجئ في استهلاك الوقود (Anomaly) في آخر 20 يومًا
- مشروع واحد يُظهر تراجعًا تدريجيًا في معدل الاستخدام

> ملاحظة: هذه بيانات اصطناعية (Synthetic) لأغراض بناء الـ Prototype. يمكن استبدالها ببيانات حقيقية
> بنفس الأعمدة إن توفرت من الفريق أو من مصدر مفتوح.

## التشغيل
```bash
pip install -r requirements.txt
python src/generate_data.py   # توليد البيانات
python src/kpis.py            # حساب المؤشرات
```

## ملخص الأدوات (Tool Functions) — Day 4
| الأداة | الوظيفة |
|---|---|
| `get_top_downtime_equipment(top_n)` | أعلى المعدات توقفًا |
| `get_equipment_needing_attention(threshold)` | معدات تحتاج تدخل فوري (downtime + صيانة شاذة، مقارنة كل معدة بنوعها) |
| `explain_utilization_trend(project)` | تحليل اتجاه الاستخدام وسببه المرجّح |
| `analyze_fuel_consumption(equipment_id)` | اكتشاف قفزات استهلاك الوقود الحديثة (Anomaly Detection بسيط) |
| `generate_fleet_report()` | تقرير أداء شامل |

## الـ Agent — Day 5
- `ask_agent(question)` في `src/agent.py`: نقطة دخول واحدة.
  - لو `OPENAI_API_KEY` موجود بالـ environment → **LLM Mode**: OpenAI Chat Completions + Function Calling الحقيقي.
  - لو مش موجود → **Built-in AI Mode**: Router محلي + Analytics + ML لنفس الأدوات، ويعمل بدون مفتاح API.
- تم اختبار الأسئلة الخمسة الأساسية من فكرة المشروع فعليًا وتعمل بشكل صحيح.

### طريقة التفعيل بمفتاح حقيقي
```bash
echo "OPENAI_API_KEY=sk-..." > .env
python src/agent.py
```

## Deliverables المطلوبة رسميًا (مسار AI + Operations)
| المطلوب | الملف/الرابط | الحالة |
|---|---|---|
| Proposal Document | `reports/FleetOps_AI_Project_Report.pdf` | ✅ جاهز |
| Model Source Code | هذا الـ repo كامل | ✅ جاهز (يحتاج رفع GitHub) |
| Test Report | `reports/FleetOps_AI_Test_Report.pdf` (16/16 اختبار ناجح، مبني من `src/test_suite.py`) | ✅ جاهز |
| Demo Video | `presentation/Demo_Video_Script.md` (سكريبت جاهز) | ⚠️ يحتاج تسجيل من المستخدم |

### Agent reliability improvements
- Respects explicit Top-N requests (for example, Top 3 returns exactly 3 results).
- Preserves named project filters in utilization questions.
- Validates equipment IDs instead of silently falling back to another unit.
- Returns reason + recommended action for maintenance and Attention Score rankings.
- Fleet reports include three manager actions.
- Built-in mode responds in Arabic when the user asks in Arabic.
