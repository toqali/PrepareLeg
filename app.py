"""
نظام مقارنة التشريعات القانونية
مقارنة شاملة بين بيانات قسطاس والديوان التشريعي
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import json

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="نظام مقارنة التشريعات القانونية",
    page_icon="Scale",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("نوع التشريع")
option = st.sidebar.radio(
    "اختر نوع البيانات:",
    ["نظام", "قانون", "تعليمات", "اتفاقيات"],
)

# ==================== الثوابت ====================
DATA_FILE = 'comparison_data.json'
PROGRESS_FILE = 'progress_data.json'
QisShownCols = ['LegName', 'LegNumber', 'Year','Replaced For', 'Canceled By','ActiveDate', 'EndDate', 'Replaced By', 'Status','Magazine_Date']
DiwShownCols = ['ByLawName', 'ByLawNumber', 'Year', 'Replaced_For', 'Magazine_Date', 'Active_Date', 'Status']

# ==================== تحميل البيانات (تم تعديله بالكامل - مسارات ثابتة وصحيحة) ====================
@st.cache_data
def load_csv_data(kind: str):
    """تحميل ملفات Excel من مسارات ثابتة ومحددة بدقة"""
    
    PATHS = {
        'نظام': {
            'qis': r'extData/Bylaws/Qis_ByLaws_V2.xlsx',
            'diwan': r'extData/Bylaws/Diwan_ByLaws_V2.xlsx'
        },
        'قانون': {
            'qis': r'extData/Laws/Qis_Laws_V2.xlsx',
            'diwan': r'extData/Laws/Diwan_Laws_V2.xlsx'
        },
        'تعليمات': {
            'qis': r'extData/Instructions/Qis_Instructions.xlsx',
            'diwan': r'extData/Instructions/Diwan_Instructions.xlsx'
        },
        'اتفاقيات': { 
            'qis': r'extData/Agreements/Qis_Agreements.xlsx',
            'diwan': r'extData/Agreements/Diwan_Agreements.xlsx'
        }
    }

    if kind not in PATHS:
        st.error(f"النوع '{kind}' غير مدعوم بعد.")
        return None, None

    qis_path = PATHS[kind]['qis']
    diwan_path = PATHS[kind]['diwan']

    def read_excel_safely(path, source_name):
        if not os.path.exists(path):
            st.error(f"غير موجود ← {path}")
            return None
        try:
            df = pd.read_excel(path)
            st.sidebar.success(f"{source_name} ({os.path.basename(path)})")
            return df
        except Exception as e:
            st.error(f"فشل تحميل {source_name}:\n{path}\n\n{str(e)}")
            return None

    qis_df = read_excel_safely(qis_path, "قسطاس")
    diwan_df = read_excel_safely(diwan_path, "الديوان")

    if qis_df is None or diwan_df is None:
        st.stop()

    return qis_df, diwan_df

# ==================== باقي الكود كما هو تمامًا (لم يتم حذفه أو تغييره) ====================

def save_to_file(filename: str, data) -> None:
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {str(e)}")

def load_from_file(filename: str):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
    return None

class SessionManager:
    @staticmethod
    def initialize():
        if 'comparison_data' not in st.session_state:
            saved = load_from_file(DATA_FILE)
            st.session_state.comparison_data = saved if saved else []
        if 'current_index' not in st.session_state:
            saved = load_from_file(PROGRESS_FILE)
            st.session_state.current_index = saved if saved else 0
        if 'show_custom_form' not in st.session_state:
            st.session_state.show_custom_form = False
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False

    @staticmethod
    def save_persistent():
        try:
            save_to_file(DATA_FILE, st.session_state.comparison_data)
            save_to_file(PROGRESS_FILE, st.session_state.current_index)
        except Exception:
            pass

def parse_status(val):
    if val is None: return None
    if isinstance(val, (int, float)):
        try: return int(val)
        except: return None
    try:
        v = str(val).strip()
        if v == '': return None
        if v == 'غير ساري': return 2
        if v.isdigit(): return int(v)
        f = float(v.replace(',', '.'))
        return int(f)
    except Exception:
        return None

def initialize_session_state():
    SessionManager.initialize()

def save_persistent_data():
    SessionManager.save_persistent()

def get_legislation_data(index: int, source_df: pd.DataFrame) -> dict:
    if index >= len(source_df):
        return {}
    row = source_df.iloc[index]
    return {k: ('' if pd.isna(v) else v) for k, v in row.to_dict().items()}

def save_comparison_record(data: dict, source: str) -> None:
    new_record = {
        'تاريخ الإدخال': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'المصدر الصحيح': source,
        **data
    }
    st.session_state.comparison_data.append(new_record)
    save_persistent_data()

def move_to_next_record(total_records: int, current_index: int) -> None:
    if current_index + 1 < total_records:
        st.session_state.current_index += 1
        save_persistent_data()
        st.rerun()
    else:
        st.balloons()
        st.success(f"تم الانتهاء من جميع السجلات!")

def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        * {font-family: 'Cairo', sans-serif; direction: rtl;}
        body, .stApp {font-size: 18px;}
        .main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;}
        .stApp {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}
        .main > div > div > div > div, .main h1, .main h2, .main h3:not(.comparison-card h3) {color: white !important;}
        .css-1d391kg, [data-testid="stSidebar"] {background: rgba(255, 255, 255, 0.1) !important;}
        [data-testid="stSidebar"] * {color: white !important;}
        .title-container {background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; margin-bottom: 2rem;}
        .comparison-card {background: rgba(255, 255, 255, 0.95); padding: 1.5rem; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin: 1rem 0;}
        .comparison-card * {color: #2d3748 !important;}
        .comparison-card h3, .comparison-card h4 {color: #667eea !important;}
        .stButton>button {width: 100%; background: white !important; color: #667eea !important; border: 3px solid #667eea !important; padding: 1rem; border-radius: 10px; font-weight: 700; font-size: 1.2em; box-shadow: 0 4px 15px rgba(0,0,0,0.2);}
        .stButton>button:hover {transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); background: #667eea !important; color: white !important;}
        .stTabs [data-baseweb="tab-list"] {background: rgba(255, 255, 255, 0.15); border-radius: 10px; padding: 0.5rem;}
        .stTabs [data-baseweb="tab"] {color: white !important; font-size: 1.1em !important; font-weight: 600 !important;}
        .stTabs [aria-selected="true"] {background: rgba(255, 255, 255, 0.3) !important; border-radius: 8px;}
        p, span, label {font-size: 1.1em;}
        .dataframe {direction: rtl !important; text-align: right !important;}
        .dataframe td, .dataframe th {text-align: right !important; padding: 20px 15px !important; font-size: 1.05em !important; border: 2px solid #cbd5e0 !important; white-space: normal !important; word-wrap: break-word !important; min-width: 150px !important; line-height: 1.6 !important; vertical-align: middle !important;}
        .dataframe thead th {background: #667eea !important; color: white !important; font-weight: bold !important;}
        .dataframe tbody tr:nth-child(even) {background-color: #f7fafc !important;}
        .stTextInput label, .stSelectbox label, .stDateInput label {color: #2d3748 !important; font-weight: 600 !important; text-align: right !important;}
        .stTextInput input, .stSelectbox select {background: white !important; color: #2d3748 !important; font-size: 1.1em !important; text-align: right !important; direction: rtl !important;}
        .wizard-container {background: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 5px 20px rgba(0,0,0,0.15);}

        /* ==================== الكروت الأصلية (قسطاس والديوان) ==================== */
        .source-card {background: #ffffff; border-radius: 14px; padding: 18px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15); direction: rtl; text-align: right; border: 2.5px solid; position: relative; overflow: hidden;}
        .source-card:hover {box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2); transform: translateY(-6px);}
        .qistas-card {background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-color: #3B82F6;}
        .qistas-card h4 {color: #1E40AF !important;}
        .qistas-card::before {content: ''; position: absolute; top: 0; right: 0; width: 5px; height: 100%; background: linear-gradient(180deg, #3B82F6, #1E40AF); border-radius: 14px 0 0 14px;}
        .diwan-card {background: linear-gradient(135deg, #FEF3F2 0%, #FED7AA 100%); border-color: #F97316;}
        .diwan-card h4 {color: #B45309 !important;}
        .diwan-card::before {content: ''; position: absolute; top: 0; right: 0; width: 5px; height: 100%; background: linear-gradient(180deg, #F97316, #B45309); border-radius: 14px 0 0 14px;}
        .info-card {background: #f3f4f6; border-radius: 8px; padding: 10px 12px; border: 1.5px solid #d1d5db; margin-bottom: 8px;}
        .info-card .field-name {font-weight: 700; color: #374151; font-size: 0.92em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.4px;}
        .qistas-card .info-card .field-name {color: #1E40AF;}
        .diwan-card .info-card .field-name {color: #B45309;}
        .info-card .field-value {color: #1f2937; font-size: 0.96em; word-wrap: break-word; white-space: normal; line-height: 1.6; font-weight: 500;}

        /* ==================== جدول المقارنة - خلفية بيضاء 100% ومظهر أنيق جدًا ==================== */
        .cmp-wrapper {
            max-height: 300px;
            overflow: auto;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
            border: 1px solid #e2e8f0;
            background: white !important;
            margin: 1.5rem 0;
        }
        .cmp-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            direction: rtl;
            font-size: 0.94rem;
            table-layout: fixed;
            background: white !important;
        }
        .cmp-table thead {
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .cmp-table thead tr {
            background: #1e40af !important;  /* أزرق غامق أنيق جدًا */
        }
        .cmp-table thead th {
            color: white !important;
            padding: 16px 12px;
            text-align: center;
            font-weight: 700;
            font-size: 1.05em;
            border-bottom: 4px solid #60a5fa;
        }
        .cmp-table tbody td {
            padding: 14px 12px;
            vertical-align: middle;
            text-align: center;
            background: white !important;
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s ease;
        }
        .cmp-table tbody td:first-child {
            text-align: right !important;
            font-weight: 700;
            color: #1f2937;
            background: #f8fafc !important;
            font-size: 0.98em;
        }
        .cmp-table tbody tr:nth-child(even) td {
            background: #ffffff !important;
        }
        .cmp-table tbody tr:nth-child(odd) td {
            background: #f8fafc !important;
        }
        .cmp-table tbody tr:hover td {
            background: #dbeafe !important;  /* أزرق فاتح جدًا عند الـ hover */
        }
        .cmp-diff {
            background: #fee2e2 !important;
            font-weight: 600;
            color: #991b1b;
        }
        .empty {
            color: #94a3b8;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)



def main():
    apply_styles()
    st.markdown("""
        <div class="title-container">
            <h1 style='color: #667eea; margin: 0;'>نظام التحقق من التشريعات القانونية</h1>
            <p style='color: #718096; margin-top: 0.5rem; font-size: 18px;'>
                مقارنة شاملة بين بيانات قسطاس والديوان التشريعي
            </p>
        </div>
    """, unsafe_allow_html=True)

    initialize_session_state()
    qis_df, diw_df = load_csv_data(option)

    if qis_df is None or diwan_df is None:
        st.error("فشل تحميل البيانات. تأكد من وجود الملفات في المسارات المحددة.")
        return

    # باقي الكود كما هو...
    tab1, tab2 = st.tabs(["مقارنة تفصيلية", "البيانات المحفوظة"])
    with tab1:
        render_comparison_tab(qis_df, diw_df)
    with tab2:
        render_saved_data_tab()

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: white; padding: 1rem;'>
            <p>نظام التحقق من التشريعات القانونية © 2025</p>
        </div>
    """, unsafe_allow_html=True)



def render_wizard_steps(current_index: int, total_records: int):
    """عرض خطوات الويزارد"""
    steps_to_show = min(5, total_records)
    cols = st.columns(steps_to_show)
    
    for i in range(steps_to_show):
        if total_records <= 5:
            actual_index = i
        else:
            if current_index < 2:
                actual_index = i
            elif current_index >= total_records - 3:
                actual_index = total_records - 5 + i
            else:
                actual_index = current_index - 2 + i
        
        with cols[i]:
            if actual_index < current_index:
                circle_color = '#48bb78'
                icon = '✓'
                label_color = '#48bb78'
                label_text = 'مكتمل'
            elif actual_index == current_index:
                circle_color = '#f97316'
                icon = '▶'
                label_color = '#f97316'
                label_text = 'الحالي'
            else:
                circle_color = '#e2e8f0'
                icon = str(actual_index + 1)
                label_color = '#718096'
                label_text = 'قادم'
            
            animation_style = "animation: pulse 2s infinite;" if actual_index == current_index else ""
            
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div style="width: 60px; height: 60px; border-radius: 50%; background: {circle_color}; 
                                color: white; display: flex; align-items: center; justify-content: center; 
                                margin: 0 auto 0.5rem auto; font-weight: bold; font-size: 1.3em; 
                                box-shadow: 0 4px 10px rgba(0,0,0,0.2); {animation_style}">
                        {icon}
                    </div>
                    <div style="color: {label_color}; font-size: 0.9em; font-weight: 600;">
                        {label_text}
                    </div>
                </div>
            """, unsafe_allow_html=True)


# ==================== عرض المقارنة ====================
def render_law_comparison(qistas_df: pd.DataFrame, diwan_df: pd.DataFrame, current_index: int, total_records: int):
    """عرض مقارنة سجل محدد كجدول (اسم الحقل | قسطاس | الديوان) - يدعم جميع أنواع التشريعات تلقائيًا"""
    qistas_data = get_legislation_data(current_index, qistas_df)
    diwan_data = get_legislation_data(current_index, diwan_df)

    st.markdown("<h3 style='color: #667eea !important; text-align: center;'>المقارنة التفصيلية</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # === خريطة ذكية للأعمدة حسب نوع التشريع (الحل النهائي والأخير) ===
    FIELD_MAPPING = {
        "نظام": {
            "name_qis": "LegName",           "name_diw": "ByLawName",
            "num_qis":  "LegNumber",          "num_diw":  "ByLawNumber",
        },
        "قانون": {
            "name_qis": "LegName",           "name_diw": "Law_Name",
            "num_qis":  "LegNumber",         "num_diw":  "Law_Number",
        },
        "تعليمات": {
            "name_qis": "LegName",   "name_diw": "Instruction_Name",
            "num_qis":  "LegNumber", "num_diw":  "Instruction_Number",
        },
        "اتفاقيات": {
            "name_qis": "LegName",     "name_diw": "Agreement_Name",
            "num_qis":  "LegNumber",   "num_diw":  "Agreement_Number",
        }
    }

    # نأخذ الخريطة الصحيحة حسب النوع المختار (مع fallback آمن)
    mapping = FIELD_MAPPING.get(option, FIELD_MAPPING["نظام"])

    # الأعمدة الأساسية اللي تظهر دائمًا
    DISPLAY_FIELDS = [
        ("اسم التشريع",       mapping["name_qis"], mapping["name_diw"]),
        ("رقم التشريع",       mapping["num_qis"],  mapping["num_diw"]),
        ("السنة",              "Year",             "Year"),
        ("يحل محل",           "Replaced For",     "Replaced_For"),
        ("تاريخ الجريدة",     "Magazine_Date",    "Magazine_Date"),
        ("تاريخ السريان",     "ActiveDate",       "Active_Date"),
        ("الحالة",            "Status",           "Status"),
    ]

    # الحقول اللي تظهر فقط إذا كان Status = 2 (غير ساري)
    CONDITIONAL_FIELDS = [
        ("ألغي بواسطة",       "Canceled By",      "Canceled_By"),
        ("تاريخ الانتهاء",    "EndDate",          "EndDate"),
        ("تم استبداله بواسطة", "Replaced By",      "Replaced_By"),
    ]

    # تحليل حالة قسطاس لتحديد إظهار الحقول المشروطة
    status_q_int = parse_status(qistas_data.get('Status'))

    rows = []

    # === إضافة الحقول الأساسية ===
    for label, q_key, d_key in DISPLAY_FIELDS:
        qv = qistas_data.get(q_key, '')
        dv = diwan_data.get(d_key, '')

        q_str = '—' if pd.isna(qv) or str(qv).strip() == '' else str(qv)
        d_str = '—' if pd.isna(dv) or str(dv).strip() == '' else str(dv)

        diff_class = 'cmp-diff' if q_str != '—' and d_str != '—' and q_str != d_str else ''
        rows.append((label, q_str, d_str, diff_class))

    # === إضافة الحقول المشروطة فقط إذا كان "غير ساري" ===
    if status_q_int == 2:
        for label, q_key, d_key in CONDITIONAL_FIELDS:
            qv = qistas_data.get(q_key, '')
            dv = diwan_data.get(d_key, '') if d_key else qistas_data.get(q_key, '')

            q_str = '—' if pd.isna(qv) or str(qv).strip() == '' else str(qv)
            d_str = '—' if pd.isna(dv) or str(dv).strip() == '' else str(dv)

            # لا نعرض السطر إذا كلاهما فارغان
            if q_str == '—' and d_str == '—':
                continue

            diff_class = 'cmp-diff' if q_str != '—' and d_str != '—' and q_str != d_str else ''
            rows.append((label, q_str, d_str, diff_class))

    # === رسم الجدول النهائي ===
    if rows:
        html = ["<div class='cmp-wrapper'><table class='cmp-table'>"]
        html.append("<thead><tr><th>اسم الحقل</th><th>قسطاس</th><th>الديوان</th></tr></thead><tbody>")
        for label, qv, dv, cls in rows:
            q_td = f"<td class='{cls}'>{qv}</td>"
            d_td = f"<td class='{cls}'>{dv}</td>"
            html.append(f"<tr><td>{label}</td>{q_td}{d_td}</tr>")
        html.append("</tbody></table></div>")
        st.markdown("\n".join(html), unsafe_allow_html=True)
    else:
        st.info("لا توجد بيانات للمقارنة في هذا السجل.")

    # استدعاء الأزرار التحكم (اختيار المصدر + التنقل)
    render_selection_buttons(qistas_data, diwan_data, current_index, total_records)
    render_navigation_buttons(current_index, total_records)


def render_selection_buttons(qistas_data: dict, diwan_data: dict, current_index: int, total_records: int):
    """عرض أزرار اختيار المصدر"""
    st.markdown("---")
    st.markdown("<h3 style='color: white !important; text-align: center; margin-top: 2rem;'>❓ أيهما أكثر دقة؟</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ قسطاس صحيح", use_container_width=True, key=f"qistas_{current_index}"):
            save_comparison_record(qistas_data, 'قسطاس')
            st.success("✅ تم حفظ النتيجة من قسطاس!")
            move_to_next_record(total_records, current_index)
    
    with col2:
        if st.button("✅ الديوان صحيح", use_container_width=True, key=f"diwan_{current_index}"):
            save_comparison_record(diwan_data, 'الديوان')
            st.success("✅ تم حفظ النتيجة من الديوان!")
            move_to_next_record(total_records, current_index)
    
    with col3:
        if st.button("⚠️ لا أحد منهم", use_container_width=True, key=f"none_{current_index}"):
            st.session_state.show_custom_form = True
            st.rerun()
    
    # نموذج الإدخال المخصص
    if st.session_state.get('show_custom_form', False):
        render_custom_form(qistas_data, current_index, total_records)


def render_custom_form(reference_data: dict, current_index: int, total_records: int):
    """عرض نموذج الإدخال المخصص"""
    st.markdown("---")
    st.markdown("<h3 style='color: white !important; text-align: center;'>✍️ أدخل البيانات الصحيحة</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("custom_data_form", clear_on_submit=False):
        custom_data = {}
        
        # إنشاء حقول إدخال لكل عمود
        num_cols = 3
        columns = list(reference_data.keys())
        
        for i in range(0, len(columns), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(columns):
                    field_name = columns[i + j]
                    default_value = reference_data[field_name]
                    custom_data[field_name] = col.text_input(
                        field_name, 
                        value=str(default_value) if default_value else ""
                    )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_custom = st.form_submit_button("💾 حفظ والانتقال للتالي", use_container_width=True)
        with col2:
            cancel_custom = st.form_submit_button("❌ إلغاء", use_container_width=True)
        
        if submit_custom:
            save_comparison_record(custom_data, 'مصدر آخر')
            st.session_state.show_custom_form = False
            st.success("✅ تم حفظ البيانات المخصصة!")
            move_to_next_record(total_records, current_index)
        
        if cancel_custom:
            st.session_state.show_custom_form = False
            st.rerun()


def render_navigation_buttons(current_index: int, total_records: int):
    """عرض أزرار التنقل"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_index > 0:
            if st.button("⏮️ السابق", use_container_width=True):
                st.session_state.current_index -= 1
                st.session_state.show_custom_form = False
                save_persistent_data()
                st.rerun()
    


def render_comparison_tab(qistas_df: pd.DataFrame, diwan_df: pd.DataFrame):
    """عرض تبويب المقارنة التفصيلية"""
    st.markdown("<div class='comparison-card'>", unsafe_allow_html=True)
    
    total_records = min(len(qistas_df), len(diwan_df))
    current_index = st.session_state.current_index
    
    # شريط التقدم
    progress_percentage = int(((current_index + 1) / total_records) * 100) if total_records > 0 else 0
    st.markdown(f"""
        <div class='wizard-container'>
            <h3 style='color: #667eea; text-align: center; margin-bottom: 0.5rem;'>مقارنة التشريعات</h3>
            <p style='color: #718096; text-align: center; font-size: 1.1em; margin-bottom: 2rem;'>
                {current_index + 1} من {total_records} ({progress_percentage}%)
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # عرض الخطوات
    if total_records > 0:
        render_wizard_steps(current_index, total_records)
    
    # شريط التقدم
    st.markdown(f"""
        <div style="background: #e2e8f0; height: 15px; border-radius: 10px; overflow: hidden; margin: 1.5rem 0 2rem 0;">
            <div style="height: 100%; background: linear-gradient(90deg, #667eea 0%, #48bb78 100%); 
                        width: {progress_percentage}%; transition: width 0.5s ease; border-radius: 10px;">
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    
    if current_index < total_records:
        render_law_comparison(qistas_df, diwan_df, current_index, total_records)
    else:
        st.success(f"🎉 تم الانتهاء من مراجعة جميع السجلات!")
        if st.button("🔄 البدء من جديد", use_container_width=True):
            st.session_state.current_index = 0
            st.session_state.show_custom_form = False
            save_persistent_data()
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_saved_data_tab():
    """عرض تبويب البيانات المحفوظة"""
    st.markdown("<div class='comparison-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #667eea !important;'>📁 البيانات المحفوظة</h3>", unsafe_allow_html=True)
    
    if st.session_state.comparison_data:
        df = pd.DataFrame(st.session_state.comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # تحميل البيانات كملف Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='مقارنة التشريعات', index=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 تحميل البيانات (Excel)",
                data=buffer.getvalue(),
                file_name=f"مقارنة_تشريعات_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # المرحلة الأولى: تفعيل وضع التأكيد (زر واحد)
            if not st.session_state.get('confirm_delete', False):
                if st.button("🗑️ مسح جميع البيانات", use_container_width=True, key="start_delete"):
                    st.session_state.confirm_delete = True
                    st.rerun()   # changed from experimental_rerun -> rerun
            else:
                # عرض تحذير وأزرار التأكيد/الإلغاء
                st.warning("⚠️ سيتم حذف جميع البيانات نهائياً. هل تريد المتابعة؟")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("⚠️ تأكيد المسح (حذف نهائي)", use_container_width=True, key="confirm_delete_yes"):
                        # تنفيذ الحذف الدائم
                        st.session_state.comparison_data = []
                        st.session_state.current_index = 0
                        try:
                            if os.path.exists(DATA_FILE):
                                os.remove(DATA_FILE)
                            if os.path.exists(PROGRESS_FILE):
                                os.remove(PROGRESS_FILE)
                        except Exception:
                            pass
                        # حفظ ملفات فارغة لضمان عدم استرجاع البيانات
                        try:
                            save_to_file(DATA_FILE, [])
                            save_to_file(PROGRESS_FILE, 0)
                        except Exception:
                            pass
                        st.session_state.confirm_delete = False
                        st.success("✅ تم حذف جميع البيانات نهائياً")
                        st.rerun()   # changed from experimental_rerun -> rerun
                with c2:
                    if st.button("❌ إلغاء", use_container_width=True, key="confirm_delete_no"):
                        st.session_state.confirm_delete = False
                        st.rerun()   # changed from experimental_rerun -> rerun
    else:
        st.info("📭 لا توجد بيانات محفوظة حتى الآن")
    
    st.markdown("</div>", unsafe_allow_html=True)


def generate_side_card(data: dict, shown_cols: list, title: str, layout: str = 'grid', hide_on_status2: bool = False) -> str:
    """إنشاء HTML لكارت مصدر (قسطاس/الديوان)
    يدعم layout = 'grid' أو 'scroll' (قائمة عمودية قابلة للتمرير)
    """
    status = data.get('Status') if isinstance(data.get('Status'), (int, float)) else None

    # كلاس القاعدة
    card_classes = "source-card"
    inner_html = ""

    if layout == 'scroll':
        # اختيار كلاس مخصص اعتماداً على العنوان (قسطاس vs الديوان)
        if 'قسطاس' in title:
            card_classes += " qistas-card"
            scroll_class = "qistas-scroll"
        else:
            card_classes += " diwan-card"
            scroll_class = "diwan-scroll"

        inner_html += f"<div class='{scroll_class}'>"
        # عرض كل الحقول كصفوف عمودية واضحة (compact)
        for key in shown_cols:
            if key not in data:
                continue
            if hide_on_status2 and status == 2 and key in ('Replaced By', 'EndDate', 'Canceled By'):
                continue
            value = '' if data.get(key) is None else data.get(key)
            safe_value = str(value)
            inner_html += (
                "<div class='info-card' style='display:block;'>"
                f"<div class='field-name'>{key}</div>"
                f"<div class='field-value'>{safe_value}</div>"
                "</div>"
            )
        inner_html += "</div>"

    else:
        # الوضع الشبكي الافتراضي: بطاقات صغيرة موزعة
        inner_html += "<div class='info-grid'>"
        for key in shown_cols:
            if key not in data:
                continue
            if hide_on_status2 and status == 2 and key in ('Replaced By', 'EndDate', 'Canceled By'):
                continue
            value = '' if data.get(key) is None else data.get(key)
            safe_value = str(value)
            inner_html += (
                "<div class='info-card'>"
                f"<div class='field-name'>{key}</div>"
                f"<div class='field-value'>{safe_value}</div>"
                "</div>"
            )
        inner_html += "</div>"

    html = f"<div class='{card_classes}'><h4>{title}</h4>{inner_html}</div>"
    return html


# ==================== البرنامج الرئيسي ====================
def main():
    """الدالة الرئيسية للبرنامج"""
    # تطبيق التنسيقات
    apply_styles()
    
    # العنوان الرئيسي
    st.markdown("""
        <div class="title-container">
            <h1 style='color: #667eea; margin: 0;'>⚖️ نظام التحقق من التشريعات القانونية</h1>
            <p style='color: #718096; margin-top: 0.5rem; font-size: 18px;'>
                مقارنة شاملة بين بيانات قسطاس والديوان التشريعي
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # تهيئة البيانات
    initialize_session_state()
    
    # تحميل البيانات من CSV بحسب اختيار المستخدم
    qistas_df, diwan_df = load_csv_data(option)
    
    if isinstance(qistas_df, pd.DataFrame) and 'GroupKey' in qistas_df.columns:
        qistas_df = qistas_df.sort_values(by='GroupKey').reset_index(drop=True)
    if isinstance(diwan_df, pd.DataFrame) and 'GroupKey' in diwan_df.columns:
        diwan_df = diwan_df.sort_values(by='GroupKey').reset_index(drop=True)
    
    if qistas_df is None or diwan_df is None:
        st.error("⚠️ فشل تحميل ملفات CSV للنوع المحدد. تأكد من وجود الملفات أو تعديل مرشحات المسارات في الكود.")
        # عرض أمثلة المسارات الممكنة للمساعدة
        st.info("مسارات محتملة:\n- extData/Bylaws/... (النظام)\n- extData/Laws/... (القوانين)\n- extData/Instructions/... (التعليمات)")
        return
    

    st.sidebar.markdown("---")
    
    # التبويبات
    tab1, tab2 = st.tabs(["🔍 مقارنة تفصيلية", "📁 البيانات المحفوظة"])
    
    # ========== التبويب الأول: المقارنة التفصيلية ==========
    with tab1:
        render_comparison_tab(qistas_df, diwan_df)
    
    # ========== التبويب الثاني: البيانات المحفوظة ==========
    with tab2:
        render_saved_data_tab()
    
    # التذييل
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: white; padding: 1rem;'>
            <p>نظام التحقق من التشريعات القانونية © 2025</p>
        </div>
    """, unsafe_allow_html=True)


# ==================== تشغيل البرنامج ====================
if __name__ == "__main__":

    main()
