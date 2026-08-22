import re

filepath = r"c:\Users\wgallardo\Documents\Proyectos gravity\intranet\templates\intranet.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

js_addition = """
        let currentYear = new Date().getFullYear();
        let currentMonth = new Date().getMonth() + 1; // 1-12
        let calendarData = {};

        async function renderCalendar() {
            const label = document.getElementById('calendarMonthLabel');
            const grid = document.getElementById('calendarGrid');
            const months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
            
            if(!label || !grid) return;
            
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
                grid.innerHTML += `<div class="calendar-day" style="background:none; border:none;"></div>`;
            }
            
            const today = new Date();
            for(let d = 1; d <= daysInMonth; d++) {
                let classes = "calendar-day";
                if(today.getDate() === d && today.getMonth() + 1 === currentMonth && today.getFullYear() === currentYear) {
                    classes += " active";
                }
                
                const data = calendarData[d];
                if(data) {
                    if(data.events && data.events.length > 0) classes += " has-event";
                    if(data.birthdays && data.birthdays.length > 0) classes += " has-birthday";
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
            const bc = document.getElementById('birthdayCard');
            if(bc) bc.style.display = 'none';
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

if "function changeMonth(" not in content:
    content = content.replace("loadDashboard();", "loadDashboard();\n            renderCalendar();")
    content = content.replace("</script>", js_addition + "\n    </script>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: Injected JS logic into intranet.html")
else:
    print("Already injected")
