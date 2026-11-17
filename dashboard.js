
    // Инициализация карты: тёмная Esri Dark Gray — стабильная подложка без ключей
    const map = L.map('map', { zoomControl: false }).setView([55.775, 37.56], 12);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    }).addTo(map);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      opacity: 0.75
    }).addTo(map);

    // Изохрона реального пробега вокруг машины
    let userPos = [55.785, 37.535];
    const rangeCircle = L.circle(userPos, {
      color: '#E85002',
      weight: 1.5,
      dashArray: '8, 12',
      className: 'zh-iso',
      fillColor: '#E85002',
      fillOpacity: 0.08,
      radius: 4320
    }).addTo(map);

    // Подпись зоны доезда у метки машины (видна всегда, даже когда кольцо больше экрана)
    const isoLabel = L.marker(userPos, {
      icon: L.divIcon({ className: 'iso-label', html: '<span>432 км · зона доезда</span>', iconSize: [0, 0], iconAnchor: [0, 0] }),
      interactive: false
    }).addTo(map);

    function updateIsoLabel(km) {
      isoLabel.setLatLng(userPos);
      isoLabel.setIcon(L.divIcon({ className: 'iso-label', html: '<span>' + km + ' км · зона доезда</span>', iconSize: [0, 0], iconAnchor: [0, 0] }));
    }

    // Авто-подгонка обзора под кольцо (чтобы зона доезда влезла в экран)
    let fitTimer = null;
    function scheduleFit() {
      clearTimeout(fitTimer);
      fitTimer = setTimeout(() => {
        try { map.fitBounds(rangeCircle.getBounds(), { padding: [70, 70] }); } catch (e) {}
      }, 500);
    }

    // Тап по карте — переставить центр зоны доезда (как на проде)
    map.on('click', (e) => {
      userPos = [e.latlng.lat, e.latlng.lng];
      rangeCircle.setLatLng(userPos);
      meMarker.setLatLng(userPos);
      isoLabel.setLatLng(userPos);
      const soc = parseInt(document.getElementById('socSlider').value, 10);
      const km = Math.round(state.baseKm * (soc / 100) * state.mult);
      showToast('zone-moved');
    });

    // Точки ЭЗС в Москве
    const stations = [
      { name: 'Россети · ТЦ Авиапарк', addr: 'Ходынский б-р, 4', km: 1.4, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '18 ₽/кВт·ч', coords: [55.7902, 37.5312] },
      { name: 'Punkt E · Ленинградский пр-т', addr: 'Ленинградский пр-т, 36', km: 2.8, type: 'dc', label: '120', kw: 120, port: 'GB/T (прямой)', t80: '~31 мин', tariff: '19.5 ₽/кВт·ч', coords: [55.7915, 37.5582] },
      { name: 'Энергия Москвы · Пресня', addr: 'Пресненская наб., 8', km: 4.1, type: 'adp', label: 'CCS', kw: 90, port: 'CCS2 (адаптер)', t80: '~42 мин', tariff: 'Бесплатно', coords: [55.7495, 37.5395] },
      { name: 'Мосэнерго · Сокол', addr: 'ул. Балтийская, 5', km: 5.6, type: 'ac', label: '22', kw: 22, port: 'Type 2 AC', t80: '~2 ч 45 мин', tariff: '12 ₽/кВт·ч', coords: [55.8051, 37.5150] },
      { name: 'Hyper · Тверская', addr: 'ул. Тверская, 26', km: 6.2, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '21 ₽/кВт·ч', coords: [55.7652, 37.6045] },
      { name: 'Россети · Динамо', addr: 'ул. Правды, 24', km: 7.4, type: 'dc', label: '120', kw: 120, port: 'GB/T (прямой)', t80: '~31 мин', tariff: '17 ₽/кВт·ч', coords: [55.7840, 37.5630] },
      { name: 'Hyper · Ленинградский', addr: 'Ленинградское ш., 5', km: 8.1, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '20 ₽/кВт·ч', coords: [55.7990, 37.5400] }
    ];

    stations.forEach((st) => {
      const cls = st.type === 'dc' ? 'ev-marker-dc' : (st.type === 'adp' ? 'ev-marker-adp' : 'ev-marker-ac');
      const icon = L.divIcon({
        className: '',
        html: `<div class="${cls}">${st.label}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });
      L.marker(st.coords, { icon }).addTo(map).bindPopup(`<b>${st.name}</b>`);
    });

    // Пульсирующий маячок авто (изохрона — вокруг него)
    const meIcon = L.divIcon({
      className: '',
      html: '<div class="me-pin"><span class="me-ring"></span><span class="me-ring d2"></span><span class="me-core"></span></div>',
      iconSize: [12, 12],
      iconAnchor: [6, 6]
    });
    const meMarker = L.marker(userPos, { icon: meIcon, interactive: false }).addTo(map);

    // Слой Яндекса: точки поверх нашей базы, помечены бейджем «Я» — без переключения карт
    const YSTATIONS = [
      { coords: [55.7770, 37.6000] }, { coords: [55.7600, 37.6200] }, { coords: [55.8000, 37.4700] },
      { coords: [55.7400, 37.6100] }, { coords: [55.8200, 37.5500] }, { coords: [55.7500, 37.4800] },
      { coords: [55.8100, 37.6400] }, { coords: [55.7350, 37.4200] }, { coords: [55.7880, 37.5100] },
      { coords: [55.7700, 37.5700] }
    ];
    const yaIcon = L.divIcon({
      className: '',
      html: '<div class="ev-marker-ya">Я</div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    const yanLayer = L.layerGroup(YSTATIONS.map(y => L.marker(y.coords, { icon: yaIcon }).bindPopup('<b>Точка Яндекс.Карт</b><br>Разъемы и статус — в источнике'))).addTo(map);
    map.removeLayer(yanLayer);

    let mult = 1.0;

    const state = { baseKm: 540, pct: 80, mult: 1.0, city: 'Москва' };

    function recalc() {
      const soc = parseInt(document.getElementById('socSlider').value, 10);
      const km = Math.round(state.baseKm * (soc / 100) * state.mult);
      document.getElementById('kmDisplay').textContent = km;
      document.getElementById('pctDisplay').textContent = soc + '%';
      document.getElementById('heroFormula').textContent = state.baseKm + ' паспорт × ' + soc + '% заряд × ' + Math.round(state.mult * 100) + '% погода';
      rangeCircle.setRadius(km * 1000);
      updateIsoLabel(km);
      scheduleFit();
    }

    function onChargeInput() {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      recalc();
    }

    function setSoc(val) {
      document.getElementById('socSlider').value = val;
      document.querySelectorAll('.preset-btn').forEach(b => {
        b.classList.toggle('active', parseInt(b.textContent) === val);
      });
      recalc();
    }

    // Километры на кривой запаса: от полного заряда при каждой температуре
    const CHART_PCTS = [45, 70, 84, 97, 100, 90];
    const CHART_TEMPS = ['-20°', '-10°', '0°', '+10°', '+20°', '+30°'];
    function updateChart(base) {
      document.getElementById('passportLabel').textContent = 'Паспортный запас · ' + base + ' км';
      CHART_PCTS.forEach((p, i) => {
        const el = document.getElementById('tval' + i);
        if (el) el.textContent = Math.round(base * p / 100) + ' км';
      });
      if (chartActive >= 0) showTip(chartActive);
    }

    // Подсветка активной точки на кривой
    let chartActive = 4;
    function setChartActive(idx) {
      chartActive = idx;
      document.querySelectorAll('.chart-dot').forEach((d, i) => {
        d.setAttribute('r', i === idx ? '5' : '4');
        d.setAttribute('fill', i === idx ? '#E85002' : '#0B0B0D');
        d.setAttribute('stroke', i === idx ? '#F9F9F9' : '#E85002');
        d.setAttribute('stroke-width', i === idx ? '2.5' : '2');
        if (i === idx) { d.setAttribute('filter', 'url(#glow)'); d.classList.add('chart-dot-on'); }
        else { d.removeAttribute('filter'); d.classList.remove('chart-dot-on'); }
      });
      document.querySelectorAll('.dot-val').forEach((t, i) => {
        t.setAttribute('fill', i === idx ? '#F9F9F9' : '#8B96A5');
        t.setAttribute('font-weight', i === idx ? '700' : '600');
        t.setAttribute('font-size', i === idx ? '12' : '10.5');
      });
      document.querySelectorAll('.dot-temp').forEach((t, i) => {
        t.setAttribute('fill', i === idx ? '#F9F9F9' : '#646464');
        t.setAttribute('font-weight', i === idx ? '600' : '400');
      });
    }

    // Клик по точке кривой = пересчёт пробега при этой температуре
    function pointClick(idx) {
      const pct = CHART_PCTS[idx];
      const icon = idx <= 2 ? 'snow' : (idx === 5 ? 'thermo' : 'sun');
      state.mult = pct / 100;
      document.querySelectorAll('.scen-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('weatherTemp').textContent = CHART_TEMPS[idx];
      document.getElementById('weatherIcon').innerHTML = WICON[icon] || '';
      document.getElementById('weatherCity').textContent = state.city + ' · Погода';
      document.getElementById('impactBadge').textContent = pct < 100 ? '-' + (100 - pct) + '% от паспорта' : '100% от паспорта';
      document.getElementById('weatherBadge').textContent = CHART_TEMPS[idx] + ' · кривая';
      setChartActive(idx);
      showTip(idx);
      recalc();
    }

    // Тултип точки кривой
    function showTip(idx) {
      const d = document.getElementById('tdot' + idx);
      const tip = document.getElementById('chartTip');
      if (!d || !tip) return;
      const cx = +d.getAttribute('cx');
      const cy = +d.getAttribute('cy');
      const base = state.baseKm;
      tip.setAttribute('transform', 'translate(' + cx + ',' + (cy - 30) + ')');
      document.getElementById('tipText').textContent = CHART_TEMPS[idx] + ' · ' + Math.round(base * CHART_PCTS[idx] / 100) + ' км';
      tip.setAttribute('opacity', '1');
    }

    function hideTip() {
      document.getElementById('chartTip').setAttribute('opacity', '0');
    }

    document.querySelectorAll('.chart-dot').forEach((d, i) => {
      d.addEventListener('mouseenter', () => { if (i !== chartActive) showTip(i); });
      d.addEventListener('mouseleave', hideTip);
    });

    function setScenario(el, m, temp, icon, desc, impact, idx) {
      state.mult = m;
      document.querySelectorAll('.scen-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      document.getElementById('weatherTemp').textContent = temp;
      document.getElementById('weatherIcon').innerHTML = WICON[icon] || '';
      document.getElementById('weatherCity').textContent = state.city + ' · ' + desc;
      document.getElementById('impactBadge').textContent = impact;
      document.getElementById('weatherBadge').textContent = el.textContent + ' · ' + temp;
      setChartActive(idx);
      recalc();
    }

    function pickCityChip(el, name, count) {
      state.city = name;
      activeCity = name;
      document.getElementById('cityInput').value = name;
      document.getElementById('cityCountBadge').textContent = count + ' ЭЗС в базе';
      document.getElementById('weatherCity').textContent = name + ' · Живой прогноз';
      document.querySelectorAll('#cityChips .city-pill').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
    }

    function switchDb(mode) {
      const yandex = mode === 'yandex';
      document.getElementById('tabOurBase').classList.toggle('active', !yandex);
      document.getElementById('tabYandex').classList.toggle('active', yandex);
      // Яндекс-слой накладывается поверх нашей базы, а не заменяет ее
      if (yandex) yanLayer.addTo(map); else map.removeLayer(yanLayer);
      const fa = document.getElementById('filterArea');
      if (fa) fa.style.opacity = yandex ? '0.45' : '1';
      document.getElementById('yandexNote').style.display = yandex ? 'block' : 'none';
      showToast(yandex ? 'Слой Яндекс.Карт наложен на нашу карту' : 'Показана только наша база');
    }

    function switchView(view) {
      ['viewMap', 'viewSplit', 'viewList'].forEach(id => document.getElementById(id).classList.remove('active'));
      document.getElementById('view' + view.charAt(0).toUpperCase() + view.slice(1)).classList.add('active');
      const drawer = document.getElementById('rightDrawer');
      const table = document.getElementById('stationTable');
      drawer.style.display = view === 'split' ? 'flex' : 'none';
      table.classList.toggle('open', view === 'list');
      if (view === 'list') updateTableFade();
    }

    function focusStation(idx) {
      document.querySelectorAll('#rightDrawer .station-item').forEach((item, i) => {
        item.classList.toggle('selected', i === idx);
      });
      document.querySelectorAll('#stationRows .station-row').forEach((row, i) => {
        row.classList.toggle('selected', i === idx);
      });
      map.flyTo(stations[idx].coords, 14);
    }

    function locateUser() {
      map.flyTo(userPos, 13);
    }

    let toastTimer = null;

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
    }

    function toastMsg(key) {
      const M = {
        route: 'Открываем маршрут в Яндекс.Картах',
        memo: 'Памятка сохранена',
        link: 'Ссылка на ЭЗС скопирована',
        'filter-gbt': 'Фильтр: GB/T DC — 148 станций в Москве',
        'filter-ccs': 'Фильтр: CCS2 через переходник — 112 станций',
        'filter-ac': 'Фильтр: Type 2 AC — 58 станций',
        'filter-chademo': 'Фильтр: CHAdeMO — 4 станции'
      };
      showToast(M[key]);
    }

    function copyShareUrl() {
      const car = encodeURIComponent(document.getElementById('carModelTitle').textContent);
      const soc = document.getElementById('socSlider').value;
      const url = `https://zapashoda-ev.ru/charging/?car=${car}&soc=${soc}`;
      showToast('Ссылка с состоянием скопирована: ' + url);
    }

    const CITY_LIST = [
      { n: 'Москва', c: 318, lat: 55.7558, lng: 37.6173 },
      { n: 'Казань', c: 105, lat: 55.7961, lng: 49.1064 },
      { n: 'Санкт-Петербург', c: 91, lat: 59.9343, lng: 30.3351 },
      { n: 'Нижний Новгород', c: 78, lat: 56.3269, lng: 44.0059 },
      { n: 'Челябинск', c: 34, lat: 55.1644, lng: 61.4368 },
      { n: 'Иваново', c: 30, lat: 57.0004, lng: 40.9739 },
      { n: 'Красноярск', c: 25, lat: 56.0096, lng: 92.8525 },
      { n: 'Самара', c: 21, lat: 53.1959, lng: 50.1002 },
      { n: 'Тюмень', c: 21, lat: 57.1530, lng: 65.5343 },
      { n: 'Волгоград', c: 21, lat: 48.7080, lng: 44.5133 },
      { n: 'Владимир', c: 21, lat: 56.1290, lng: 40.4070 },
      { n: 'Тула', c: 20, lat: 54.1961, lng: 37.6182 },
      { n: 'Чебоксары', c: 19, lat: 56.1439, lng: 47.2489 },
      { n: 'Липецк', c: 19, lat: 52.6031, lng: 39.5708 },
      { n: 'Новосибирск', c: 16, lat: 55.0084, lng: 82.9357 },
      { n: 'Набережные Челны', c: 16, lat: 55.7436, lng: 52.3958 },
      { n: 'Ростов-на-Дону', c: 16, lat: 47.2357, lng: 39.7015 },
      { n: 'Кемерово', c: 15, lat: 55.3547, lng: 86.0873 },
      { n: 'Ярославль', c: 15, lat: 57.6261, lng: 39.8845 },
      { n: 'Иркутск', c: 15, lat: 52.2871, lng: 104.3050 },
      { n: 'Екатеринбург', c: 14, lat: 56.8389, lng: 60.6057 },
      { n: 'Калининград', c: 14, lat: 54.7104, lng: 20.4522 },
      { n: 'Калуга', c: 14, lat: 54.5293, lng: 36.2754 },
      { n: 'Пермь', c: 14, lat: 58.0104, lng: 56.2502 },
      { n: 'Рязань', c: 14, lat: 54.6269, lng: 39.6916 },
      { n: 'Химки', c: 12, lat: 55.8894, lng: 37.4449 },
      { n: 'Хабаровск', c: 12, lat: 48.4827, lng: 135.0838 },
      { n: 'Йошкар-Ола', c: 12, lat: 56.6388, lng: 47.8904 },
      { n: 'Краснодар', c: 11, lat: 45.0355, lng: 38.9753 },
      { n: 'Томск', c: 11, lat: 56.4846, lng: 84.9476 },
      { n: 'Нижнекамск', c: 11, lat: 55.6366, lng: 51.8245 },
      { n: 'Сочи', c: 11, lat: 43.5855, lng: 39.7231 },
      { n: 'Ульяновск', c: 10, lat: 54.3142, lng: 48.4031 },
      { n: 'Оренбург', c: 10, lat: 51.7727, lng: 55.0988 },
      { n: 'Севастополь', c: 10, lat: 44.6166, lng: 33.5254 },
      { n: 'Реутов', c: 9, lat: 55.7963, lng: 37.8581 }
    ];

    let activeCity = 'Москва';

    function pickCity(city) {
      activeCity = city.n;
      state.city = city.n;
      document.getElementById('cityInput').value = city.n;
      document.getElementById('cityCountBadge').textContent = city.c + ' ЭЗС в базе';
      document.getElementById('weatherCity').textContent = city.n + ' · Живой прогноз';
      document.querySelectorAll('.city-pill').forEach(c => c.classList.remove('active'));
      map.flyTo([city.lat, city.lng], 12);
      rangeCircle.setLatLng([city.lat, city.lng]);
      closeCitySheet();
      renderCityGrid();
    }

    function renderCityGrid() {
      document.getElementById('cityGrid').innerHTML = CITY_LIST.map(c => `
        <div class="city-cell ${c.n === activeCity ? 'active' : ''}" onclick="pickCity(${CITY_LIST.indexOf(c)})">
          ${c.n} <b>${c.c}</b>
        </div>`).join('');
    }

    function openCitySheet() {
      renderCityGrid();
      document.getElementById('citySheet').classList.add('open');
    }

    function closeCitySheet() {
      document.getElementById('citySheet').classList.remove('open');
    }

    const MODELS = [
      { name: 'Zeekr 001 · 100 кВт·ч', base: 540, port: 'GB/T DC · 200 кВт', d: true },
      { name: 'Zeekr 007 · 75 кВт·ч', base: 480, port: 'GB/T DC · 240 кВт', d: true },
      { name: 'BYD Song Plus EV', base: 460, port: 'GB/T DC · 90 кВт', d: true },
      { name: 'BYD Han EV', base: 510, port: 'GB/T DC · 120 кВт', d: true },
      { name: 'Tesla Model Y Long Range (EU)', base: 490, port: 'CCS2 · 250 кВт', d: false },
      { name: 'Tesla Model 3 Highland (EU)', base: 515, port: 'CCS2 · 250 кВт', d: false },
      { name: 'Li Auto L7 (батарея EV)', base: 180, port: 'GB/T DC · 75 кВт', d: true },
      { name: 'Avatr 11 (официально RU)', base: 525, port: 'GB/T DC · 240 кВт', d: true },
      { name: 'Xiaomi SU7 Max', base: 620, port: 'GB/T DC · 260 кВт', d: true },
      { name: 'Evolute i-Pro', base: 340, port: 'GB/T DC · 60 кВт', d: true }
    ];

    function renderModels(list) {
      document.getElementById('modelList').innerHTML = list.map(m => `
        <div class="model-option" onclick="chooseModel('${m.name}', ${m.base}, '${m.port}', ${m.d})">
          <div style="min-width: 0;">
            <div class="model-name">${m.name}</div>
            <div class="model-base">Паспортный запас: ${m.base} км</div>
          </div>
          <span class="port-tag">${m.port}</span>
        </div>`).join('');
    }

    function openCarModal() {
      renderModels(MODELS);
      document.getElementById('carModal').classList.add('open');
    }

    function closeCarModal() {
      document.getElementById('carModal').classList.remove('open');
    }

    function filterModels(q) {
      renderModels(MODELS.filter(m => m.name.toLowerCase().includes(q.toLowerCase())));
    }

    function chooseModel(name, base, port, direct) {
      state.baseKm = base;
      document.getElementById('carModelTitle').textContent = name;
      document.getElementById('carPortTag').textContent = port;
      document.getElementById('carBaseKm').textContent = 'Паспортный запас: ' + base + ' км';
      document.getElementById('compatText').textContent = direct ? 'Напрямую DC' : 'Через адаптер';
      updateChart(base);
      closeCarModal();
      recalc();
    }

    const WICON = {
      sun: '<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"/></svg>',
      snow: '<svg class="ic" viewBox="0 0 24 24"><path d="M12 3v18M5 6.5l14 11M19 6.5l-14 11M12 8l-2.2-2.2M12 8l2.2-2.2M12 16l-2.2 2.2M12 16l2.2 2.2"/></svg>',
      thermo: '<svg class="ic" viewBox="0 0 24 24"><path d="M10 13.5V5a2 2 0 1 1 4 0v8.5a4.5 4.5 0 1 1-4 0z"/></svg>',
      road: '<svg class="ic" viewBox="0 0 24 24"><path d="M6 3l3 18M18 3l-3 18M12 5v3M12 11v3M12 17v3"/></svg>'
    };

    function openRoute(i) {
      const st = stations[i];
      const url = 'https://yandex.ru/maps/?rtext=' + encodeURIComponent(userPos[0] + ',' + userPos[1] + '~' + st.coords[0] + ',' + st.coords[1]) + '&rtt=auto';
      showToast('route-open');
      window.open(url, '_blank');
    }

    function renderCards() {
      document.getElementById('rightDrawer').innerHTML = stations.map((s, i) => `
        <div class="station-item ${i === 0 ? 'selected' : ''}" id="stCard${i}" onclick="focusStation(${i})">
          <div class="st-top">
            <div style="min-width: 0;">
              <div class="st-name">${s.name}</div>
              <div class="st-addr">${s.addr} · ${s.km} км</div>
            </div>
            <div class="st-kw"${s.type === 'adp' ? ' style="color: var(--sand-gold);"' : (s.type === 'ac' ? ' style="color: var(--green);"' : '')}>${s.kw} кВт</div>
          </div>
          <div class="st-metrics">
            <div>
              <div class="st-m-label">Разъем</div>
              <div class="st-m-val" style="color: ${s.type === 'dc' ? 'var(--orange)' : (s.type === 'adp' ? 'var(--sand-gold)' : 'var(--green)')};">${s.port}</div>
            </div>
            <div>
              <div class="st-m-label">До 80%</div>
              <div class="st-m-val">${s.t80}</div>
            </div>
            <div>
              <div class="st-m-label">Тариф</div>
              <div class="st-m-val"${s.tariff === 'Бесплатно' ? ' style="color: var(--green);"' : ''}>${s.tariff}</div>
            </div>
          </div>
          <div class="st-actions">
            <button class="btn-route" onclick="event.stopPropagation(); openRoute(${i})">Маршрут в Яндекс</button>
            <button class="btn-ghost" onclick="event.stopPropagation(); toastMsg('memo')">Памятка</button>
            <button class="btn-ghost" onclick="event.stopPropagation(); toastMsg('link')">Ссылка</button>
          </div>
        </div>`).join('');
    }

    function renderTable() {
      document.getElementById('stationRows').innerHTML = stations.map((s, i) => `
        <div class="station-row ${i === 0 ? 'selected' : ''}" onclick="focusStation(${i})">
          <div><div class="r-name">${s.name}</div><div class="r-addr">${s.addr}</div></div>
          <div class="r-col">Расстояние<b>${s.km} км</b></div>
          <div class="r-col">Порт<b>${s.port}</b></div>
          <div class="r-col">До 80%<b>${s.t80}</b></div>
          <div class="r-col">Тариф<b>${s.tariff}</b></div>
          <span class="st-kw-mini"${s.type === 'adp' ? ' style="color: var(--sand-gold);"' : (s.type === 'ac' ? ' style="color: var(--green);"' : '')}>${s.kw} кВт</span>
        </div>`).join('');
      updateTableFade();
    }

    function updateTableFade() {
      const wrap = document.getElementById('stationTable');
      wrap.classList.toggle('fade-bottom', wrap.scrollTop + wrap.clientHeight < wrap.scrollHeight - 4);
    }

    document.getElementById('stationTable').addEventListener('scroll', updateTableFade);

    renderCards();
    renderTable();
    document.getElementById('weatherIcon').innerHTML = WICON.sun;
    recalc();
  