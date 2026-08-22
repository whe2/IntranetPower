import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\intranet.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update HTML Structure for calendar
target_html = """                <div class="calendar-wrapper">
                    <div class="calendar-header-month">Julio 2026</div>
                    <div class="calendar-grid">
                        <div class="calendar-day-name">L</div>
                        <div class="calendar-day-name">M</div>
                        <div class="calendar-day-name">X</div>
                        <div class="calendar-day-name">J</div>
                        <div class="calendar-day-name">V</div>
                        <div class="calendar-day-name">S</div>
                        <div class="calendar-day-name">D</div>
                        <div class="calendar-day"></div>
                        <div class="calendar-day"></div>
                        <div class="calendar-day">1</div>
                        <div class="calendar-day">2</div>
                        <div class="calendar-day">3</div>
                        <div class="calendar-day">4</div>
                        <div class="calendar-day">5</div>
                        <div class="calendar-day">6</div>
                        <div class="calendar-day">7</div>
                        <div class="calendar-day">8</div>
                        <div class="calendar-day">9</div>
                        <div class="calendar-day">10</div>
                        <div class="calendar-day">11</div>
                        <div class="calendar-day">12</div>
                        <div class="calendar-day">13</div>
                        <div class="calendar-day">14</div>
                        <div class="calendar-day active" id="activeDay">15</div>
                        <div class="calendar-day">16</div>
                        <div class="calendar-day">17</div>
                        <div class="calendar-day">18</div>
                        <div class="calendar-day">19</div>
                        <div class="calendar-day">20</div>
                        <div class="calendar-day">21</div>
                        <div class="calendar-day">22</div>
                        <div class="calendar-day">23</div>
                        <div class="calendar-day">24</div>
                        <div class="calendar-day">25</div>
                        <div class="calendar-day">26</div>
                        <div class="calendar-day">27</div>
                        <div class="calendar-day">28</div>
                        <div class="calendar-day">29</div>
                        <div class="calendar-day">30</div>
                        <div class="calendar-day">31</div>
                    </div>
                </div>

                <div class="birthday-card" id="birthdayCard">
                    <img id="birthdayPhoto"
                        src="https://ngfihmioixtfnrmlrlam.supabase.co/storage/v1/object/public/power/Gemini_Generated_Image_glf24lglf24lglf2.png"
                        alt="Cumpleañero">
                    <div class="birthday-info">
                        <h4>🎂 Próximo Cumpleaños</h4>
                        <p><strong id="birthdayName">Carlos Mendoza</strong></p>
                        <p><small id="birthdayDate">18 de Julio</small></p>
                    </div>
                </div>"""

new_html = """                <div class="calendar-wrapper">
                    <div class="calendar-header-month" style="display:flex; justify-content:space-between; align-items:center;">
                        <button onclick="changeMonth(-1)" style="background:none; border:none; cursor:pointer; font-size:18px; color:var(--texto-gris);"><i class="fa-solid fa-chevron-left"></i></button>
                        <span id="calendarMonthLabel">Cargando...</span>
                        <button onclick="changeMonth(1)" style="background:none; border:none; cursor:pointer; font-size:18px; color:var(--texto-gris);"><i class="fa-solid fa-chevron-right"></i></button>
                    </div>
                    <div class="calendar-grid" id="calendarGrid">
                        <!-- Generado por JS -->
                    </div>
                </div>

                <div class="birthday-card" id="birthdayCard" style="display:none; flex-direction:column; gap:10px; align-items:flex-start;">
                    <div style="display:flex; justify-content:space-between; width:100%; align-items:center;">
                        <h4 style="margin:0; font-size:14px; color:var(--texto-negro);"><i class="fa-solid fa-calendar-day" style="color:var(--acento);"></i> Detalle del Día</h4>
                        <button onclick="document.getElementById('birthdayCard').style.display='none'" style="background:none; border:none; cursor:pointer; color:#ef4444;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div id="calendarDayDetails" style="width:100%; display:flex; flex-direction:column; gap:8px;">
                        <!-- JS injected -->
                    </div>
                </div>"""

if target_html in content:
    content = content.replace(target_html, new_html)

# 2. Add CSS
css_target = ".calendar-day.active {"
css_addition = """        .calendar-day {
            cursor: pointer;
            position: relative;
            transition: background 0.2s;
        }
        .calendar-day:hover {
            background-color: #e2e8f0;
        }
        .calendar-day.has-event {
            border: 2px solid var(--acento);
        }
        .calendar-day.has-birthday::after {
            content: "🎂";
            position: absolute;
            top: -5px;
            right: -5px;
            font-size: 10px;
        }
        .calendar-day.active {"""

if css_target in content:
    content = content.replace("        .calendar-day.active {", css_addition)


# 3. Add JS logic
js_target = "async function loadIntranetData() {"
js_addition = """
        let currentYear = new Date().getFullYear();
        let currentMonth = new Date().getMonth() + 1; // 1-12
        let calendarData = {};

        async function renderCalendar() {
            const label = document.getElementById('calendarMonthLabel');
            const grid = document.getElementById('calendarGrid');
            const months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
            label.textContent = `${months[currentMonth - 1]} ${currentYear}`;
            
            // Header days
            grid.innerHTML = `
                <div class="calendar-day-name">L</div>
                <div class="calendar-day-name">M</div>
                <div class="calendar-day-name">X</div>
                <div class="calendar-day-name">J</div>
                <div class="calendar-day-name">V</div>
                <div class="calendar-day-name">S</div>
                <div class="calendar-day-name">D</div>
            `;
            
            // Fetch data
            try {
                const res = await fetch(`/api/intranet/calendar?year=${currentYear}&month=${currentMonth}`);
                if (res.ok) calendarData = await res.json();
                else calendarData = {};
            } catch(e) { calendarData = {}; }

            const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();
            const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
            
            // Adjust to start on Monday
            let emptyDays = firstDay === 0 ? 6 : firstDay - 1;
            
            for(let i = 0; i < emptyDays; i++) {
                grid.innerHTML += `<div class="calendar-day" style="background:none;"></div>`;
            }
            
            const today = new Date();
            for(let d = 1; d <= daysInMonth; d++) {
                let classes = "calendar-day";
                if(today.getDate() === d && today.getMonth() + 1 === currentMonth && today.getFullYear() === currentYear) {
                    classes += " active";
                }
                
                const data = calendarData[d];
                if(data) {
                    if(data.events.length > 0) classes += " has-event";
                    if(data.birthdays.length > 0) classes += " has-birthday";
                }
                
                grid.innerHTML += `<div class="${classes}" onclick="showDayDetails(${d})">${d}</div>`;
            }
        }

        function changeMonth(delta) {
            currentMonth += delta;
            if(currentMonth > 12) {
                currentMonth = 1;
                currentYear++;
            } else if(currentMonth < 1) {
                currentMonth = 12;
                currentYear--;
            }
            renderCalendar();
            document.getElementById('birthdayCard').style.display = 'none';
        }

        function showDayDetails(day) {
            const card = document.getElementById('birthdayCard');
            const container = document.getElementById('calendarDayDetails');
            const data = calendarData[day];
            
            if(!data || (data.events.length === 0 && data.birthdays.length === 0)) {
                // No events
                container.innerHTML = `<p style="font-size:13px; color:var(--texto-gris); text-align:center;">No hay eventos para este día.</p>`;
            } else {
                let html = '';
                if(data.birthdays.length > 0) {
                    html += `<div><strong style="color:var(--acento); font-size:12px;">CUMPLEAÑOS</strong>`;
                    data.birthdays.forEach(b => {
                        html += `
                        <div style="display:flex; align-items:center; gap:10px; margin-top:5px; background:#fff; padding:5px; border-radius:6px; border:1px solid #e2e8f0;">
                            <img src="${b.photo_url}" style="width:30px; height:30px; border-radius:50%; object-fit:cover;">
                            <div>
                                <div style="font-size:12px; font-weight:bold;">${b.name}</div>
                                <div style="font-size:10px; color:#64748b;">${b.department}</div>
                            </div>
                        </div>`;
                    });
                    html += `</div>`;
                }
                if(data.events.length > 0) {
                    html += `<div style="margin-top:10px;"><strong style="color:#ef4444; font-size:12px;">ACTIVIDADES</strong>`;
                    data.events.forEach(e => {
                        html += `
                        <div style="margin-top:5px; background:#fff; padding:8px; border-radius:6px; border:1px solid #e2e8f0; border-left:3px solid #ef4444;">
                            <div style="font-size:12px; font-weight:bold;">${e.title}</div>
                            ${e.description ? `<div style="font-size:11px; color:#64748b; margin-top:3px;">${e.description}</div>` : ''}
                        </div>`;
                    });
                    html += `</div>`;
                }
                container.innerHTML = html;
            }
            card.style.display = 'flex';
        }
"""

if js_target in content:
    content = content.replace(js_target, js_addition + "\n        " + js_target)

# We also need to call renderCalendar() on init
init_target = "loadIntranetData();"
if init_target in content and "renderCalendar();" not in content:
    content = content.replace(init_target, "loadIntranetData();\n        renderCalendar();")


with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated intranet.html calendar logic")
