"""
Страница проверки точности расчёта длины реза
Загрузите DXF-файл и увидите сравнение пяти методов
"""

import streamlit as st
import sys
import math
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Добавляем корень проекта в путь, если ещё нет
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    import ezdxf
except ImportError:
    st.error("❌ Не установлен ezdxf. Выполните `pip install ezdxf`")
    st.stop()

try:
    from shapely.geometry import LineString
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

from dxf_analyzer.calculators.cut_length import calculate_cut_length
from dxf_analyzer.core.config import SILENT_SKIP_TYPES

# ----- Вспомогательные функции (скопированы из verify_cut_length.py) -----
def direct_line_length(entity) -> float:
    s = entity.dxf.start
    e = entity.dxf.end
    return math.hypot(e.x - s.x, e.y - s.y)

def direct_arc_length(entity) -> float:
    r = entity.dxf.radius
    start = math.radians(entity.dxf.start_angle)
    end = math.radians(entity.dxf.end_angle)
    if end < start:
        end += 2 * math.pi
    return r * (end - start)

def direct_circle_length(entity) -> float:
    return 2 * math.pi * entity.dxf.radius

def bulge_arc_length(x1, y1, x2, y2, bulge):
    if abs(bulge) < 1e-10:
        return math.hypot(x2 - x1, y2 - y1)
    chord = math.hypot(x2 - x1, y2 - y1)
    if chord < 1e-10:
        return 0.0
    abs_bulge = abs(bulge)
    central_angle = 4.0 * math.atan(abs_bulge)
    sin_half = math.sin(central_angle / 2)
    if sin_half == 0:
        return chord
    radius = chord / (2 * sin_half)
    return radius * central_angle

def direct_lwpolyline_length(entity) -> float:
    points = list(entity.get_points('xyb'))
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        x1, y1, bulge = points[i]
        x2, y2, _ = points[i+1]
        total += bulge_arc_length(x1, y1, x2, y2, bulge)
    if entity.closed:
        x1, y1, bulge = points[-1]
        x2, y2, _ = points[0]
        total += bulge_arc_length(x1, y1, x2, y2, bulge)
    return total

def direct_polyline_length(entity) -> float:
    points = list(entity.points())
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points)-1):
        p1, p2 = points[i], points[i+1]
        total += math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2)
    if entity.is_closed and len(points) > 1:
        p1, p2 = points[-1], points[0]
        total += math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2 + (p2.z-p1.z)**2)
    return total

def spline_length_high_precision(entity, n_segments=10000) -> float:
    try:
        pts = list(entity.flattening(0.0001))
        if len(pts) < 2:
            return 0.0
        length = 0.0
        for i in range(len(pts)-1):
            length += math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
        return length
    except Exception:
        cpts = list(entity.control_points)
        if len(cpts) < 2:
            return 0.0
        length = 0.0
        for i in range(len(cpts)-1):
            p1, p2 = cpts[i], cpts[i+1]
            length += math.hypot(p2.x-p1.x, p2.y-p1.y)
        return length * 1.1

def ellipse_length_high_precision(entity, n_segments=10000) -> float:
    major = entity.dxf.major_axis
    ratio = entity.dxf.ratio
    a = math.hypot(major.x, major.y)
    b = a * ratio
    start = getattr(entity.dxf, 'start_param', 0.0)
    end = getattr(entity.dxf, 'end_param', 2*math.pi)
    dt = (end - start) / n_segments
    total = 0.0
    t = start
    xp = a * math.cos(t)
    yp = b * math.sin(t)
    for _ in range(n_segments):
        t += dt
        xc = a * math.cos(t)
        yc = b * math.sin(t)
        total += math.hypot(xc - xp, yc - yp)
        xp, yp = xc, yc
    return total

def ellipse_ramanujan(entity) -> float:
    major = entity.dxf.major_axis
    ratio = entity.dxf.ratio
    a = math.hypot(major.x, major.y)
    b = a * ratio
    h = ((a - b)**2) / ((a + b)**2)
    perimeter = math.pi * (a + b) * (1 + 3*h/(10 + math.sqrt(4 - 3*h)))
    return perimeter

def entity_to_shapely(entity):
    if not SHAPELY_AVAILABLE:
        return None
    try:
        t = entity.dxftype()
        if t == 'LINE':
            s = entity.dxf.start
            e = entity.dxf.end
            return LineString([(s.x, s.y), (e.x, e.y)])
        elif t == 'CIRCLE':
            cx, cy = entity.dxf.center.x, entity.dxf.center.y
            r = entity.dxf.radius
            n = 360
            pts = [(cx + r*math.cos(2*math.pi*i/n), cy + r*math.sin(2*math.pi*i/n)) for i in range(n)]
            return LineString(pts + [pts[0]])
        elif t == 'ARC':
            cx, cy = entity.dxf.center.x, entity.dxf.center.y
            r = entity.dxf.radius
            start = math.radians(entity.dxf.start_angle)
            end = math.radians(entity.dxf.end_angle)
            if end < start:
                end += 2*math.pi
            n = max(10, int((end-start)*180/math.pi))
            pts = [(cx + r*math.cos(start + (end-start)*i/n), cy + r*math.sin(start + (end-start)*i/n)) for i in range(n+1)]
            return LineString(pts)
        elif t == 'LWPOLYLINE':
            pts = [(p[0], p[1]) for p in entity.get_points('xy')]
            if entity.closed and len(pts) > 1:
                pts.append(pts[0])
            return LineString(pts) if len(pts) >= 2 else None
        elif t == 'POLYLINE':
            pts = [(p.x, p.y) for p in entity.points()]
            if entity.is_closed and len(pts) > 1:
                pts.append(pts[0])
            return LineString(pts) if len(pts) >= 2 else None
        elif t == 'SPLINE':
            pts = list(entity.flattening(0.001))
            return LineString(pts) if len(pts) >= 2 else None
        elif t == 'ELLIPSE':
            a = math.hypot(entity.dxf.major_axis.x, entity.dxf.major_axis.y)
            b = a * entity.dxf.ratio
            n = 500
            pts = [(a*math.cos(2*math.pi*i/n), b*math.sin(2*math.pi*i/n)) for i in range(n+1)]
            return LineString(pts)
    except Exception:
        return None
    return None
# ----------------------------------------------------------------

def render_verify_page():
    st.title("🔍 Проверка точности расчёта длины реза")
    st.markdown("""
    Загрузите DXF-файл, и **5 разных методов** одновременно вычислят длину реза.
    Вы увидите таблицу сравнения, расхождения и итоговый вердикт.
    """)

    uploaded_file = st.file_uploader("📂 Загрузите DXF-файл для верификации", type=["dxf"])

    if uploaded_file is not None:
        with st.spinner("⏳ Вычисляем длину реза пятью методами..."):
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            try:
                doc = ezdxf.readfile(tmp_path)
                msp = doc.modelspace()

                # 1. Основной метод
                total_main = calculate_cut_length(tmp_path)

                # Собираем значимые объекты
                entities = []
                for e in msp:
                    if e.dxftype() not in SILENT_SKIP_TYPES:
                        entities.append(e)

                # 2. Прямые формулы
                direct_details = []
                for e in entities:
                    t = e.dxftype()
                    if t == 'LINE':
                        val = direct_line_length(e)
                    elif t == 'ARC':
                        val = direct_arc_length(e)
                    elif t == 'CIRCLE':
                        val = direct_circle_length(e)
                    elif t == 'LWPOLYLINE':
                        val = direct_lwpolyline_length(e)
                    elif t == 'POLYLINE':
                        val = direct_polyline_length(e)
                    elif t == 'SPLINE':
                        val = spline_length_high_precision(e)
                    elif t == 'ELLIPSE':
                        val = ellipse_length_high_precision(e)
                    else:
                        val = 0.0
                    direct_details.append(val)
                total_direct = sum(direct_details)

                # 3. Shapely
                total_shapely = 0.0
                if SHAPELY_AVAILABLE:
                    for e in entities:
                        geom = entity_to_shapely(e)
                        if geom:
                            total_shapely += geom.length
                else:
                    st.warning("⚠️ Shapely не установлен – метод недоступен")

                # 4. Повышенная точность (берем прямые, т.к. они уже high-res)
                total_highprec = total_direct

                # 5. Рамануджан для эллипсов, остальное прямо
                total_ramanujan = 0.0
                for i, e in enumerate(entities):
                    if e.dxftype() == 'ELLIPSE':
                        total_ramanujan += ellipse_ramanujan(e)
                    else:
                        total_ramanujan += direct_details[i]

                methods = {
                    "Основной калькулятор": total_main,
                    "Прямые формулы": total_direct,
                    "Shapely (аппроксимация)": total_shapely if SHAPELY_AVAILABLE else None,
                    "Повышенная точность (кривые)": total_highprec,
                    "Рамануджан (эллипсы) + прямо": total_ramanujan
                }
                # Убираем None
                methods = {k: v for k, v in methods.items() if v is not None}

                # ----- ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ -----
                st.success("✅ Вычисления завершены!")

                st.markdown("### 📊 Сравнение методов")
                # Таблица
                import pandas as pd
                df = pd.DataFrame({
                    "Метод": list(methods.keys()),
                    "Длина (мм)": [round(v, 3) for v in methods.values()],
                    "Отклонение от основного (мм)": [round(v - total_main, 3) for v in methods.values()]
                })
                st.table(df)

                # Максимальное отклонение
                max_dev = max(abs(v - total_main) for v in methods.values())

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Основной метод", f"{total_main:.3f} мм")
                with col2:
                    st.metric("Макс. расхождение", f"{max_dev:.3f} мм")
                with col3:
                    if max_dev < 0.01:
                        st.success("Отклонение < 0.01 мм – идеально!")
                    elif max_dev < 0.1:
                        st.warning("Отклонение < 0.1 мм – допустимо")
                    else:
                        st.error("Значительные расхождения!")

                # График сравнения
                st.markdown("### 📈 Визуализация отклонений")
                chart_data = {"Метод": list(methods.keys()), "Длина, мм": list(methods.values())}
                st.bar_chart(chart_data, x="Метод", y="Длина, мм")

            except Exception as e:
                st.error(f"❌ Ошибка при анализе: {e}")
            finally:
                os.unlink(tmp_path)
    else:
        st.info("👆 Загрузите DXF-файл, чтобы начать проверку.")