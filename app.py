# app.py
"""
Главное приложение DXF Analyzer
"""

import streamlit as st
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))


def show_main_page():
    """Главная страница (встроенная версия)"""
    st.title("🏠 DXF Analyzer - Главная страница")
    
    st.markdown("""
    ## Добро пожаловать в DXF Analyzer!
    
    Это приложение для анализа DXF файлов и расчёта длины реза для плазменной резки металла.
    
    ### 📋 Возможности:
    - 📏 Расчёт длины реза 2D фигур
    - 📊 Анализ геометрии деталей
    - 📦 Оптимизация раскроя листового материала
    - 🧪 Тестирование точности расчётов
    
    ### 🚀 Начало работы:
    1. Выберите нужную функцию в боковом меню
    2. Загрузите DXF файл
    3. Получите результаты анализа
    
    ### 📚 Документация:
    Подробная документация доступна в разделе "Документация"
    """)
    
    # Быстрый старт
    st.markdown("---")
    st.subheader("⚡ Быстрый старт")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📏 Расчёт длины реза**
        
        Загрузите DXF файл и получите:
        - Общую длину реза
        - Длину по слоям
        - Количество прожигов
        - Детальную таблицу
        """)
    
    with col2:
        st.info("""
        **🧪 Проверка точности**
        
        Протестируйте точность на эталонных фигурах:
        - 10 тестовых примеров
        - Визуальные отчёты
        - Экспорт результатов
        """)


def show_testing_page():
    """Страница тестирования"""
    st.title("🧪 Тестирование точности расчётов")
    
    # Проверка наличия тестовых файлов
    tests_dir = Path("tests")
    fixtures_dir = tests_dir / "fixtures"
    
    if not tests_dir.exists() or not fixtures_dir.exists():
        st.warning("""
        ⚠️ **Тестовая среда не настроена**
        
        Для использования тестов необходимо:
        1. Создать директорию `tests/fixtures/`
        2. Сгенерировать тестовые файлы
        """)
        
        if st.button("⚙️ Создать тестовую среду"):
            with st.spinner("Создание директорий..."):
                tests_dir.mkdir(exist_ok=True)
                fixtures_dir.mkdir(exist_ok=True)
            st.success("✅ Директории созданы!")
            st.info("Теперь нажмите кнопку 'Настроить тесты' ниже")
    
    st.markdown("""
    Эта страница позволяет проверить точность расчёта длины реза на 10 эталонных фигурах.
    
    **Проверяемые фигуры:**
    1. Круг Ø200мм
    2. Прямоугольник 300×200мм
    3. Квадрат 250×250мм
    4. Треугольник (сторона 150мм)
    5. Шестигранник (под ключ 100мм)
    6. Фланец с отверстиями
    7. Кронштейн L-образный
    8. Кольцо (шайба)
    9. Продолговатое отверстие
    10. Сложная деталь
    """)
    
    # Кнопки управления
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        run_button = st.button("▶️ Запустить тесты", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🔄 Сбросить", use_container_width=True):
            if 'test_results' in st.session_state:
                del st.session_state.test_results
            st.rerun()
    
    with col3:
        setup_tests = st.button("⚙️ Настроить тесты", use_container_width=True)
    
    # Настройка тестов
    if setup_tests:
        with st.spinner("Генерация тестовых файлов..."):
            try:
                # Импорт с обработкой ошибок
                try:
                    from tests.generate_test_fixtures import TestFixturesGenerator
                    from tests.create_expected_results import create_expected_results
                except ImportError as e:
                    st.error(f"""
                    ❌ Ошибка импорта модулей тестирования: {str(e)}
                    
                    Убедитесь, что файлы существуют:
                    - tests/generate_test_fixtures.py
                    - tests/create_expected_results.py
                    """)
                    return
                
                # Генерация фикстур
                generator = TestFixturesGenerator()
                generator.create_all_fixtures()
                
                # Создание эталонных данных
                create_expected_results()
                
                st.success("✅ Тестовые файлы успешно созданы!")
                st.info("Теперь можете запустить тесты")
                
            except Exception as e:
                st.error(f"❌ Ошибка при настройке тестов: {str(e)}")
                st.exception(e)
    
    # Запуск тестов
    if run_button:
        import json
        import time
        
        # Проверка наличия эталонных данных
        expected_file = fixtures_dir / "expected_results.json"
        
        if not expected_file.exists():
            st.error("""
            ❌ Файл эталонных данных не найден!
            
            Нажмите кнопку "⚙️ Настроить тесты" для создания тестовых файлов.
            """)
            return
        
        # Загрузка эталонных данных
        try:
            with open(expected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_cases = data['test_cases']
        except Exception as e:
            st.error(f"❌ Ошибка загрузки эталонных данных: {str(e)}")
            return
        
        # Прогресс
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("⏳ Запуск тестов...")
        
        # Импорт необходимых модулей
        try:
            from dxf_analyzer.parsers.dxf_reader import DXFReader
            from dxf_analyzer.calculators.registry import CalculatorRegistry
        except ImportError as e:
            st.error(f"❌ Ошибка импорта модулей DXF Analyzer: {str(e)}")
            return
        
        # Функция расчёта
        def calculate_cut_length(file_path: str) -> float:
            reader = DXFReader()
            entities = reader.read(file_path)
            
            registry = CalculatorRegistry()
            total_length = 0.0
            
            for entity in entities:
                entity_type = entity.dxftype()
                calculator = registry.get_calculator(entity_type)
                
                if calculator:
                    length = calculator.calculate_length(entity)
                    total_length += length
            
            return total_length
        
        # Результаты тестов
        results = []
        
        # Запуск тестов
        for i, test_case in enumerate(test_cases):
            progress_bar.progress((i + 1) / len(test_cases))
            status_text.text(f"⏳ Тест {i+1}/{len(test_cases)}: {test_case['name']}")
            
            file_path = fixtures_dir / test_case['file']
            
            start_time = time.time()
            
            result = {
                'id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'expected': test_case['expected_length'],
                'tolerance': test_case['tolerance'],
                'actual': None,
                'passed': False,
                'error': None,
                'duration': 0
            }
            
            if not file_path.exists():
                result['error'] = f"Файл не найден: {test_case['file']}"
                results.append(result)
                continue
            
            try:
                # Расчёт длины
                actual = calculate_cut_length(str(file_path))
                expected = test_case['expected_length']
                tolerance = test_case['tolerance']
                
                # Проверка
                diff = abs(actual - expected)
                passed = diff <= tolerance
                
                result['actual'] = actual
                result['passed'] = passed
                result['difference'] = diff
                result['duration'] = time.time() - start_time
                
            except Exception as e:
                result['error'] = str(e)
                result['duration'] = time.time() - start_time
            
            results.append(result)
        
        # Сохраняем результаты
        st.session_state.test_results = results
        
        progress_bar.progress(100)
        status_text.text("✅ Тесты завершены!")
    
    # Отображение результатов
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        
        # Статистика
        passed = sum(1 for r in results if r['passed'])
        failed = sum(1 for r in results if not r['passed'] and not r['error'])
        errors = sum(1 for r in results if r['error'])
        total = len(results)
        
        # Метрики
        st.markdown("---")
        st.subheader("📊 Итоговая статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего тестов", total)
        
        with col2:
            st.metric("Пройдено", passed, delta=f"{passed/total*100:.1f}%")
        
        with col3:
            st.metric("Провалено", failed, delta=f"-{failed/total*100:.1f}%" if failed > 0 else "0%")
        
        with col4:
            st.metric("Ошибки", errors)
        
        # Прогресс-бар
        progress_percent = passed / total if total > 0 else 0
        st.progress(progress_percent)
        
        if progress_percent == 1.0:
            st.success("🎉 Все тесты пройдены успешно!")
        elif progress_percent >= 0.8:
            st.warning("⚠️ Большинство тестов пройдено, но есть проблемы")
        else:
            st.error("❌ Обнаружены серьёзные проблемы с расчётами")
        
        # Детальная таблица
        st.markdown("---")
        st.subheader("📋 Детальные результаты")
        
        # Таблица результатов
        for result in results:
            # Цвет карточки
            if result['error']:
                card_color = "#fff3cd"
                icon = "⚠️"
                border_color = "#856404"
            elif result['passed']:
                card_color = "#d4edda"
                icon = "✅"
                border_color = "#28a745"
            else:
                card_color = "#f8d7da"
                icon = "❌"
                border_color = "#dc3545"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: {card_color};
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-left: 5px solid {border_color};
                ">
                    <h4>{icon} Тест #{result['id']}: {result['name']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Файл:** `{result['file']}`")
                
                with col2:
                    st.write(f"**Ожидаемо:** {result['expected']:.2f} мм")
                
                with col3:
                    if result['actual'] is not None:
                        st.write(f"**Получено:** {result['actual']:.2f} мм")
                    else:
                        st.write(f"**Получено:** N/A")
                
                with col4:
                    if result.get('difference') is not None:
                        diff_color = "green" if result['passed'] else "red"
                        st.write(f"**Разница:** :{diff_color}[{result['difference']:.3f} мм]")
                    else:
                        st.write(f"**Разница:** N/A")
                
                # Детали ошибки
                if result['error']:
                    with st.expander("🔍 Детали ошибки"):
                        st.code(result['error'], language="text")
                
                st.markdown("---")
        
        # Экспорт результатов
        st.markdown("---")
        st.subheader("💾 Экспорт результатов")
        
        import json
        
        json_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": f"{passed/total*100:.1f}%"
            },
            "results": results
        }
        
        st.download_button(
            label="📥 Скачать JSON",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
            file_name=f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def show_docs_page():
    """Страница документации"""
    st.title("📚 Документация")
    
    st.markdown("""
    ## Руководство пользователя DXF Analyzer
    
    ### 1. Расчёт длины реза
    
    #### Поддерживаемые типы объектов:
    - **LINE** - прямые линии
    - **CIRCLE** - окружности
    - **ARC** - дуги
    - **LWPOLYLINE** - легковесные полилинии
    - **POLYLINE** - полилинии
    - **SPLINE** - сплайны
    - **ELLIPSE** - эллипсы
    
    #### Формулы расчёта:
    
    **Окружность:**
    ```
    L = 2 × π × R
    где R - радиус
    ```
    
    **Дуга:**
    ```
    L = (θ / 360°) × 2 × π × R
    где θ - угол дуги в градусах
    ```
    
    **Прямая линия:**
    ```
    L = √((x₂-x₁)² + (y₂-y₁)²)
    ```
    
    ### 2. Тестирование
    
    Модуль тестирования проверяет точность расчётов на эталонных фигурах:
    
    1. **Настройка тестов** - создание тестовых DXF файлов
    2. **Запуск тестов** - автоматическая проверка 10 фигур
    3. **Просмотр результатов** - детальный отчёт с визуализацией
    4. **Экспорт** - сохранение результатов в JSON
    
    ### 3. Советы по использованию
    
    #### Подготовка DXF файлов:
    - Используйте единицы измерения в миллиметрах
    - Убедитесь, что все контуры замкнуты
    - Избегайте дублирования линий
    - Проверьте масштаб чертежа
    
    #### Интерпретация результатов:
    - **Общая длина** - сумма всех контуров
    - **По слоям** - длина по каждому слою отдельно
    - **Количество прожигов** - число отдельных контуров
    - **Граница** - габаритные размеры детали
    
    ### 4. Часто задаваемые вопросы
    
    **Q: Почему длина отличается от CAD-системы?**  
    A: Проверьте единицы измерения и точность аппроксимации сплайнов.
    
    **Q: Как учитывается толщина реза?**  
    A: Приложение рассчитывает геометрическую длину. Для учёта керфа добавьте корректировку вручную.
    
    **Q: Можно ли обрабатывать 3D модели?**  
    A: Нет, поддерживаются только 2D объекты в плоскости XY.
    
    ### 5. Техническая поддержка
    
    По вопросам обращайтесь:
    - 📧 Email: support@example.com
    - 🐛 Issues: GitHub repository
    - 📖 Wiki: Подробная документация
    """)


def main():
    """Главная функция приложения"""
    
    st.set_page_config(
        page_title="DXF Analyzer",
        page_icon="📐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Боковое меню
    with st.sidebar:
        st.title("📐 DXF Analyzer")
        st.markdown("---")
        
        page = st.radio(
            "Навигация",
            [
                "🏠 Главная",
                "📚 Документация",
                "🧪 Тестирование"
            ]
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ О приложении")
        st.markdown("""
        **Версия:** 2.0.0  
        **Автор:** DXF Analyzer Team  
        **Лицензия:** MIT
        """)
        
        # Ссылки
        st.markdown("---")
        st.markdown("### 🔗 Полезные ссылки")
        st.markdown("""
        - [GitHub](https://github.com/yourusername/dxf-analyzer)
        - [Документация](https://docs.example.com)
        - [Сообщить об ошибке](https://github.com/yourusername/dxf-analyzer/issues)
        """)
    
    # Отображение выбранной страницы
    try:
        if page == "🏠 Главная":
            show_main_page()
        elif page == "📚 Документация":
            show_docs_page()
        elif page == "🧪 Тестирование":
            show_testing_page()
    except Exception as e:
        st.error(f"❌ Ошибка загрузки страницы: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()
