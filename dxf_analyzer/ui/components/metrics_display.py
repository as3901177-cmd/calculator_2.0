"""
Компоненты отображения метрик
"""

import streamlit as st
from typing import Dict, Any


def display_summary_metrics(total_length: float, num_objects: int, piercing_count: int):
    """Отображение сводных метрик"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Миллиметры", f"{total_length:.2f}")
    
    with col2:
        st.metric("Сантиметры", f"{total_length/10:.2f}")
    
    with col3:
        st.metric("Метры", f"{total_length/1000:.4f}")
    
    with col4:
        st.metric("Объектов", f"{num_objects}")
    
    with col5:
        st.metric("🔵 Врезок (цепей)", f"{piercing_count}")


def display_piercing_metrics(piercing_details: Dict[str, Any]):
    """Отображение метрик статистики врезок"""
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    
    with col_p1:
        st.metric(
            "🔵 Всего цепей",
            piercing_details['total'],
            help="Количество связанных групп объектов"
        )
    
    with col_p2:
        st.metric(
            "🔴 Замкнутые",
            piercing_details['closed_objects'],
            help="Полные контуры"
        )
    
    with col_p3:
        st.metric(
            "🔗 Открытые группы",
            piercing_details['open_chains'],
            help="Несколько связанных открытых объектов"
        )
    
    with col_p4:
        st.metric(
            "➡️ Изолированные",
            piercing_details['isolated_objects'],
            help="Одиночные открытые объекты"
        )
    
    with col_p5:
        st.metric(
            "⚙️ Допуск",
            f"{piercing_details['tolerance_used']} мм",
            help="Точки ближе этого значения считаются соединёнными"
        )
