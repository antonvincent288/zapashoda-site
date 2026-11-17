
    // Инициализация карты: тёмная Esri Dark Gray — стабильная подложка без ключей
    const map = L.map('map', { zoomControl: false, keepBuffer: 1, updateWhenZooming: false, preferCanvas: true }).setView([55.775, 37.56], 12);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      updateWhenIdle: true
    }).addTo(map);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      opacity: 0.75,
      updateWhenIdle: true
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
      // Тач-зона: тап в радиусе ~48px от станции открывает её карточку, а не переставляет зону
      if (STATIONS_DB && STATIONS_DB.length) {
        try {
          const pt = map.latLngToLayerPoint(e.latlng);
          let best = null, bestD = 24;
          STATIONS_DB.forEach((x) => {
            if (typeof x.lat !== 'number' || typeof x.lon !== 'number') return;
            const p = map.latLngToLayerPoint([x.lat, x.lon]);
            const d = Math.hypot(p.x - pt.x, p.y - pt.y);
            if (d < bestD) { bestD = d; best = x; }
          });
          if (best) {
            L.popup().setLatLng([best.lat, best.lon]).setContent('<div class="st-pop">'
              + '<div class="st-pop-name">' + (best.op || best.n || 'ЭЗС') + (best.src === 'ya' ? ' · Я' : '') + '</div>'
              + '<div class="st-pop-addr">' + (best.a || '') + '</div>'
              + (best.src === 'yandex' ? '<div class="st-pop-src">Источник: Яндекс.Карты — мощность и порты могут отсутствовать</div>' : (best.src === 'osm' ? '<div class="st-pop-src">Источник: OpenStreetMap — мощность и порты могут отсутствовать</div>' : ''))
              + '<div class="st-pop-grid"><div><span>Мощность</span><b>' + kwLabel(best.pw) + '</b></div><div><span>Порты</span><b>' + (best.s && best.s.length ? best.s.join(', ') : '—') + '</b></div></div>'
              + '<a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=' + encodeURIComponent(userPos[0] + ',' + userPos[1] + '~' + best.lat + ',' + best.lon) + '&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>'
              + '</div>').openOn(map);
            return;
          }
        } catch (err) {}
      }
      if (introMode) introMode = false;
      userPos = [e.latlng.lat, e.latlng.lng];
      rangeCircle.setLatLng(userPos);
      meMarker.setLatLng(userPos);
      isoLabel.setLatLng(userPos);
      const soc = parseInt(document.getElementById('socSlider').value, 10);
      const km = Math.round(state.baseKm * (soc / 100) * state.mult);
      showToast('zone-moved');
    });

    // Точки ЭЗС в Москве
    let stations = [
      { name: 'Россети · ТЦ Авиапарк', addr: 'Ходынский б-р, 4', km: 1.4, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '18 ₽/кВт·ч', coords: [55.7902, 37.5312] },
      { name: 'Punkt E · Ленинградский пр-т', addr: 'Ленинградский пр-т, 36', km: 2.8, type: 'dc', label: '120', kw: 120, port: 'GB/T (прямой)', t80: '~31 мин', tariff: '19.5 ₽/кВт·ч', coords: [55.7915, 37.5582] },
      { name: 'Энергия Москвы · Пресня', addr: 'Пресненская наб., 8', km: 4.1, type: 'adp', label: 'CCS', kw: 90, port: 'CCS2 (адаптер)', t80: '~42 мин', tariff: 'Бесплатно', coords: [55.7495, 37.5395] },
      { name: 'Мосэнерго · Сокол', addr: 'ул. Балтийская, 5', km: 5.6, type: 'ac', label: '22', kw: 22, port: 'Type 2 AC', t80: '~2 ч 45 мин', tariff: '12 ₽/кВт·ч', coords: [55.8051, 37.5150] },
      { name: 'Hyper · Тверская', addr: 'ул. Тверская, 26', km: 6.2, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '21 ₽/кВт·ч', coords: [55.7652, 37.6045] },
      { name: 'Россети · Динамо', addr: 'ул. Правды, 24', km: 7.4, type: 'dc', label: '120', kw: 120, port: 'GB/T (прямой)', t80: '~31 мин', tariff: '17 ₽/кВт·ч', coords: [55.7840, 37.5630] },
      { name: 'Hyper · Ленинградский', addr: 'Ленинградское ш., 5', km: 8.1, type: 'dc', label: '150', kw: 150, port: 'GB/T (прямой)', t80: '~24 мин', tariff: '20 ₽/кВт·ч', coords: [55.7990, 37.5400] }
    ];

    const stLayer = L.layerGroup().addTo(map);

    function stCls(t) {
      return t === 'dc' ? 'ev-marker-dc' : (t === 'adp' ? 'ev-marker-adp' : (t === 'ac' ? 'ev-marker-ac' : 'ev-marker-na'));
    }

    function addStationMarkers() {
      stLayer.clearLayers();
      stations.forEach((st) => {
        const icon = st.type === 'na'
          ? L.divIcon({ className: '', html: '<div style="width:28px;height:28px;display:flex;align-items:center;justify-content:center"><div class="ev-marker-na"></div></div>', iconSize: [28, 28], iconAnchor: [14, 14] })
          : L.divIcon({ className: '', html: `<div style="width:44px;height:44px;display:flex;align-items:center;justify-content:center"><div class="${stCls(st.type)}">${st.label}</div></div>`, iconSize: [44, 44], iconAnchor: [22, 22] });
        const m = L.marker(st.coords, { icon }).addTo(stLayer);
        m.bindPopup(`<div class="st-pop">
          <div class="st-pop-name">${st.name}</div>
          <div class="st-pop-addr">${st.addr}</div>
          <div class="st-pop-grid">
            <div><span>Расстояние</span><b>${st.km} км</b></div>
            <div><span>Мощность</span><b>${kwLabel(st.kw)}</b></div>
            <div><span>0→80%</span><b>${st.t80}</b></div>
            <div><span>Тариф</span><b>${st.tariff || tariffLabel(st)}</b></div>
          </div>
          <div class="st-pop-row">Порты: ${st.port}</div>
          <a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=${encodeURIComponent(userPos[0] + ',' + userPos[1] + '~' + st.coords[0] + ',' + st.coords[1])}&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>
        </div>`, { maxWidth: 250 });
        m.on('click', () => { const i = stations.indexOf(st); if (i >= 0) focusStation(i); });
      });
    }

    addStationMarkers();

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

    const state = { baseKm: 540, pct: 80, mult: 1.0, city: 'Москва', roundTrip: false };

    function recalc(fit) {
      if (introMode) {
        // Стартовый вид: кольцо 2 км, карта — центр города в радиусе 10 км.
        // Крупные события (fit=true) выводят из интро; слайдер — только цифры.
        if (fit) {
          introMode = false;
        } else {
          const soc = parseInt(document.getElementById('socSlider').value, 10);
          const km = Math.round(state.baseKm * (soc / 100) * state.mult * (state.roundTrip ? 0.5 : 1));
          document.getElementById('kmDisplay').textContent = km;
          document.getElementById('pctDisplay').textContent = soc + '%';
          return;
        }
      }
      const soc = parseInt(document.getElementById('socSlider').value, 10);
      const km = Math.round(state.baseKm * (soc / 100) * state.mult * (state.roundTrip ? 0.5 : 1));
      document.getElementById('kmDisplay').textContent = km;
      document.getElementById('pctDisplay').textContent = soc + '%';
      document.getElementById('heroFormula').textContent = state.baseKm + ' паспорт × ' + soc + '% заряд × ' + Math.round(state.mult * 100) + '% погода' + (state.roundTrip ? ' × туда-обратно' : '');
      rangeCircle.setRadius(km * 1000);
      updateIsoLabel(km);
      // Авто-подгонка обзора — только по крупным событиям (точка кривой, сценарий, модель, погода).
      // При движении слайдера карту НЕ дёргаем: это давало непрерывную перерисовку и тормоза.
      if (fit) scheduleFit();
    }

        function onChargeInput() {
      if (introMode) exitIntro();
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
      recalc(true);
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
      recalc(true);
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
      const s = stations[idx];
      const tbl = document.getElementById('stationTable');
      if (tbl && getComputedStyle(tbl).display !== 'none') mView('map');
      setTimeout(() => {
        try {
          L.popup().setLatLng(s.coords).setContent('<div class="st-pop">'
            + '<div class="st-pop-name">' + (s.op || s.n || s.name || 'ЭЗС') + '</div>'
            + '<div class="st-pop-addr">' + (s.a || s.addr || '') + '</div>'
            + '<div class="st-pop-grid"><div><span>Мощность</span><b>' + (s.tariff ? s.tariff : (Number(s.pw) ? Number(s.pw) + ' кВт' : '—')) + '</b></div><div><span>Порты</span><b>' + (s.port || (s.s && s.s.length ? s.s.join(', ') : '—')) + '</b></div></div>'
            + '<a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=' + encodeURIComponent(userPos[0] + ',' + userPos[1] + '~' + s.coords[0] + ',' + s.coords[1]) + '&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>'
            + '</div>').openOn(map);
        } catch (e) {}
      }, 950);
    }

    function locateUser() {
      map.flyTo(userPos, 13);
    }

    // === Полный каталог моделей с прода (154) + умный поиск ===
    let MODELS_ALL = null;

    async function loadModelsCatalog() {
      try {
        const r = await fetch('/models.json', { cache: 'no-cache' });
        if (!r.ok) return;
        const d = await r.json();
        MODELS_ALL = (d.models || []).map(m => ({
          name: m.name, slug: m.slug, brand: m.brand, url: m.url,
          base: m.base, cap: m.cap,
          port: (m.direct ? 'GB/T DC' : (m.port || '') + ' (адаптер)').trim(),
          d: !!m.direct, est: m.base != null
        }));
      } catch (e) {}
    }

    function normStr(str) {
      return (str || '').toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]/g, '');
    }

    const KBD = {q:'й', w:'ц', e:'у', r:'к', t:'е', y:'н', u:'г', i:'ш', o:'щ', p:'з', a:'ф', s:'ы', d:'в', f:'а', g:'п', h:'р', j:'о', k:'л', l:'д', z:'я', x:'ч', c:'с', v:'м', b:'и', n:'т', m:'ь'};
    const TRANSL = {a:'а', b:'б', v:'в', g:'г', d:'д', e:'е', z:'з', i:'и', k:'к', l:'л', m:'м', n:'н', o:'о', p:'п', r:'р', s:'с', t:'т', u:'у', f:'ф', h:'х', c:'ц', y:'ы', j:'й', w:'в', q:'к', x:'кс'};

    const KBD_REV = {}; Object.keys(KBD).forEach(k => { if (!KBD_REV[KBD[k]]) KBD_REV[KBD[k]] = k; });
    const TRANSL_REV = {}; Object.keys(TRANSL).forEach(k => { if (!TRANSL_REV[TRANSL[k]]) TRANSL_REV[TRANSL[k]] = k; });

    function layoutTo(str) { return [...str].map(ch => KBD[ch] || ch).join(''); }
    function layoutFrom(str) { return [...str].map(ch => KBD_REV[ch] || ch).join(''); }
    function translit(str) { return [...str].map(ch => TRANSL[ch] || ch).join(''); }
    function translitFrom(str) { return [...str].map(ch => TRANSL_REV[ch] || ch).join(''); }

    function hammingLE1(a, b) {
      if (!a || a.length !== b.length) return false;
      let diff = 0;
      for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) { diff++; if (diff > 1) return false; }
      }
      return true;
    }

    function modelScore(m, q) {
      const nq = normStr(q);
      if (!nq) return 1;
      const nm = normStr(m.name || ''), nb = normStr(m.brand || '');
      let best = 0;
      new Set([nq, layoutTo(nq), layoutFrom(nq), translit(nq), translitFrom(nq)]).forEach(qq => {
        if (nm.includes(qq)) best = Math.max(best, 100 - Math.min(20, nm.length - qq.length));
        if (nm.startsWith(qq)) best = Math.max(best, 95);
        if (nb && nb.includes(qq)) best = Math.max(best, 80);
        if (qq.length >= 3 && hammingLE1(nm.slice(0, qq.length), qq)) best = Math.max(best, 70);
      });
      return best;
    }

    function filterModels(q) {
      const list = MODELS_ALL || MODELS;
      if (!q || !q.trim()) { renderModels(list.slice(0, 60)); return; }
      const scored = list
        .map(m => ({ m: m, s: modelScore(m, q) }))
        .filter(x => x.s > 0)
        .sort((a, b) => b.s - a.s)
        .slice(0, 60);
      renderModels(scored.map(x => x.m));
    }

    function renderModels(list) {
      const cnt = document.getElementById('modelCount');
      if (cnt) cnt.textContent = (MODELS_ALL ? MODELS_ALL.length : list.length) + ' моделей';
      document.getElementById('modelList').innerHTML = list.map(m => {
        const base = m.base;
        const baseTxt = base
          ? (m.est ? '≈ ' + base + ' км (оценка по ёмкости)' : 'Паспортный запас: ' + base + ' км')
          : 'Ёмкость батареи не указана — см. карточку модели';
        const click = base
          ? `chooseModelModel('${(m.name || '').replace(/'/g, "\'")}', ${base}, '${(m.port || '').replace(/'/g, "\'")}', ${m.d ? 'true' : 'false'}, ${m.est ? 'true' : 'false'})`
          : `window.open('${m.url}', '_blank')`;
        return `
        <div class="model-option ${base ? '' : 'model-option-na'}" onclick="${click}">
          <div style="min-width: 0;">
            <div class="model-name">${m.name}</div>
            <div class="model-base">${baseTxt}</div>
          </div>
          <span class="port-tag">${m.port || '—'}</span>
        </div>`;
      }).join('');
    }

    function chooseModelModel(name, base, port, direct, est) {
      chooseModel(name, base, port, direct, est);
    }

    function openCarModal() {
      filterModels('');
      document.getElementById('carModal').classList.add('open');
    }

    // === Погода по гео: open-meteo ===
    async function loadWeather() {
      if (weatherDone) return;
      const noGeo = !userPos;
      if (noGeo) showToast('Не определили ваш город — погода по Москве. Тап по бейджу погоды — повторим');
      try {
        const cached = JSON.parse(localStorage.getItem('zh-weather-dash') || 'null');
        if (cached && cached.city === state.city && typeof cached.t === 'number' && Date.now() - cached.ts < 30 * 60 * 1000) {
          weatherDone = true;
          applyWeatherTemp(cached.t, 'кэш');
          return;
        }
      } catch (e) {}
      try {
        const r = noGeo ? null : await fetch('https://api.open-meteo.com/v1/forecast?latitude=' + userPos[0].toFixed(3) + '&longitude=' + userPos[1].toFixed(3) + '&current=temperature_2m', { cache: 'no-store' });
        const d = await r.json();
        const t = d && d.current && typeof d.current.temperature_2m === 'number' ? Math.round(d.current.temperature_2m) : null;
        if (t !== null) { weatherDone = true; saveWeatherCache(t); applyWeatherTemp(t, 'open-meteo'); return; }
      } catch (e) {}
      try {
        const r2 = noGeo ? null : await fetch('https://wttr.in/' + userPos[1].toFixed(2) + ',' + userPos[0].toFixed(2) + '?format=j1', { cache: 'no-store' });
        const d2 = await r2.json();
        const tc = d2 && d2.current_condition && d2.current_condition[0] ? parseInt(d2.current_condition[0].temp_C, 10) : null;
        if (tc !== null && !isNaN(tc)) { weatherDone = true; saveWeatherCache(tc); applyWeatherTemp(tc, 'wttr.in'); return; }
      } catch (e) {}
      try {
        const r3 = await fetch('/charging/weather.json', { cache: 'no-cache' });
        const d3 = await r3.json();
        const cities = (d3 && d3.cities) || {};
        let bestName = null, bestD = 1e9;
        if (userPos) {
          (CITY_LIST || []).forEach(c => {
            if (!cities[c.n]) return;
            const dx = (c.lat - userPos[0]) * 111;
            const dy = (c.lng - userPos[1]) * 111 * Math.cos(userPos[0] * Math.PI / 180);
            const d = Math.hypot(dx, dy);
            if (d < bestD) { bestD = d; bestName = c.n; }
          });
        }
        if (!bestName) bestName = (state.city && cities[state.city]) ? state.city : 'Москва';
        const hit = cities[bestName];
        if (hit && typeof hit.t === 'number') {
          weatherDone = true;
          applyWeatherTemp(Math.round(hit.t), bestD < 1e8 ? 'ближайший: ' + bestName : 'кэш: ' + bestName);
          return;
        }
      } catch (e) {}
      showToast('Погода недоступна — показана база +20°C. Тап по бейджу погоды — повторим');
    }

    function retryWeather() {
      weatherDone = false;
      loadWeather();
    }

    function saveWeatherCache(t) {
      try { localStorage.setItem('zh-weather-dash', JSON.stringify({ city: state.city, t: t, ts: Date.now() })); } catch (e) {}
    }

    // PWA: установка одним тапом
    let deferredPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const b = document.getElementById('pwaInstall');
      if (b) b.style.display = 'flex';
    });
    function pwaInstall() {
      if (deferredPrompt) { deferredPrompt.prompt(); deferredPrompt = null; }
      else showToast('Установка уже доступна через меню браузера: «На экран „Домой“»');
    }
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    function applyWeatherTemp(t, src) {
      let idx = 4, best = 1e9;
      CHART_TEMPS.forEach((ct, i) => {
        const num = parseFloat(String(ct).replace('+', '').replace('°', ''));
        if (!isFinite(num)) return;
        const d = Math.abs(num - t);
        if (d < best) { best = d; idx = i; }
      });
      const pct = CHART_PCTS[idx];
      state.mult = pct / 100;
      const lbl = t > 0 ? '+' + t : String(t);
      const wi = document.getElementById('weatherIcon');
      if (wi) wi.innerHTML = t <= 0 ? WICON.snow : WICON.sun;
      document.getElementById('weatherBadge').textContent = lbl + '° · погода';
      const ib = document.getElementById('impactBadge');
      if (ib) ib.textContent = (pct < 100 ? '−' + Math.round(100 - pct) : '100') + '% от нормы';
      setChartActive(idx);
      recalc(false);
      const gt = document.getElementById('barGeoText');
      if (gt) gt.textContent = (state.city || '') + ' · ' + lbl + '°';
      // тост погоды убран: чип «город · °C» уже живёт в шапке
    }

    function kwLabel(v) {
      return (v != null && v !== '') ? (v + ' кВт') : '—';
    }

    function typeColor(t) {
      return t === 'dc' ? 'var(--orange)' : (t === 'adp' ? 'var(--sand-gold)' : (t === 'ac' ? 'var(--green)' : 'var(--text-dim)'));
    }

    function typeBg(t) {
      return t === 'dc' ? 'rgba(232, 80, 2, 0.14)' : (t === 'adp' ? 'rgba(217, 195, 171, 0.14)' : (t === 'ac' ? 'rgba(16, 185, 129, 0.14)' : 'rgba(148, 163, 184, 0.12)'));
    }

    // === Мобильная навигация как в приложении ===
    function setActiveTab(id) {
      document.querySelectorAll('.mobile-tabbar .tab').forEach(t => t.classList.remove('active'));
      const el = document.getElementById(id);
      if (el) el.classList.add('active');
    }

    function mView(view) {
      if (view === 'map') {
        document.querySelector('.hud-left').classList.remove('open');
        switchView('map');
        setActiveTab('tabMapM');
      } else if (view === 'stations') {
        switchView('list');
        setActiveTab('tabStationsM');
      } else if (view === 'car') {
        switchView('map');
        document.querySelector('.hud-left').classList.add('open');
        setActiveTab('tabCarM');
      }
    }

    function openSideMenu() {
      document.getElementById('sideMenu').classList.add('show');
      document.getElementById('sideOverlay').classList.add('show');
    }

    function closeSideMenu() {
      document.getElementById('sideMenu').classList.remove('show');
      document.getElementById('sideOverlay').classList.remove('show');
    }

    function resetCar() {
      const title = document.getElementById('carModelTitle');
      if (title.textContent === 'Выберите модель') {
        showToast('Поле уже чистое — выберите модель из каталога');
        return;
      }
      title.textContent = 'Выберите модель';
      document.getElementById('carPortTag').textContent = '—';
      document.getElementById('carBaseKm').textContent = 'Расчёт держится по последней выбранной модели';
      document.getElementById('compatText').textContent = '—';
      showToast('Сброшено — поле чистое. Модели: каталог 154');
    }

    function toggleStack() {
      const el = document.querySelector('.hud-left');
      if (el) el.classList.toggle('open');
    }

    // === Единая смена города: карта, метка, кольцо, подписи ===
    function setCityView(name, lat, lng, count) {
      state.city = name;
      const inp = document.getElementById('cityInput');
      if (inp && document.activeElement !== inp) inp.value = name;
      if (count != null) document.getElementById('cityCountBadge').textContent = count + ' ЭЗС в базе';
      document.getElementById('weatherCity').textContent = name + ' · Живой прогноз';
      userPos = [lat, lng];
      map.flyTo(userPos, 12);
      rangeCircle.setLatLng(userPos);
      meMarker.setLatLng(userPos);
      isoLabel.setLatLng(userPos);
      const gtChip = document.getElementById('barGeoText');
      if (gtChip) gtChip.textContent = name;
      showToast('Город: ' + name);
      enterIntro();
      if (STATIONS_DB) renderNearby();
    }

    function pickCity(city) {
      activeCity = city.n;
      document.querySelectorAll('.city-pill').forEach(c => c.classList.remove('active'));
      setCityView(city.n, city.lat, city.lng, city.c);
      closeCitySheet();
      renderCityGrid();
    }

    function pickCityChip(el, name, count) {
      activeCity = name;
      document.querySelectorAll('#cityChips .city-pill').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      const hit = CITY_LIST.find(c => c.n === name);
      if (hit) setCityView(name, hit.lat, hit.lng, count);
      else {
        document.getElementById('cityInput').value = name;
        document.getElementById('cityCountBadge').textContent = count + ' ЭЗС в базе';
        document.getElementById('weatherCity').textContent = name + ' · Живой прогноз';
      }
    }

    function citySearch() {
      const q = (document.getElementById('cityInput').value || '').trim();
      if (!q) return;
      const hit = CITY_LIST.find(c => c.n.toLowerCase() === q.toLowerCase());
      if (hit) { pickCity(hit); return; }
      geocodeCity(q);
    }

    async function geocodeCity(q) {
      try {
        const r = await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&accept-language=ru&q=' + encodeURIComponent(q + ', Россия'));
        const d = await r.json();
        if (d && d[0]) {
          const lat = parseFloat(d[0].lat), lon = parseFloat(d[0].lon);
          activeCity = q;
          setCityView(q, lat, lon);
        } else {
          showToast('Город не найден в геокодере');
        }
      } catch (e) {
        showToast('Геокодер недоступен — попробуйте ещё раз');
      }
    }

    // === Гео по IP при первом заходе ===
    let geoApplied = false;
    async function loadGeoCity() {
      if (geoApplied) return;
      let g = null;
      try {
        const r = await fetch('https://ipwho.is/', { cache: 'no-store' });
        const d = await r.json();
        if (d && d.success !== false && d.city && isFinite(d.latitude)) g = { city: d.city, lat: d.latitude, lng: d.longitude };
      } catch (e) {}
      if (!g) {
        try {
          const r = await fetch('https://get.geojs.io/v1/ip/geo.json', { cache: 'no-store' });
          const d = await r.json();
          if (d && d.city) g = { city: d.city, lat: parseFloat(d.latitude), lng: parseFloat(d.longitude) };
        } catch (e) {}
      }
      if (!g || geoApplied) {
        showToast('Не определили ваш город — выберите его в панели снизу');
        return;
      }
      if (g) {
        const hitCity = CITY_LIST.find(c => c.n === g.city || String(c.n).toLowerCase() === String(g.city).toLowerCase());
        if (hitCity) {
          g.city = hitCity.n;
        } else {
          /* имя города из гео не подменяем: показываем как определилось (Шереметьево, аэропорт и т.п.) */
        }
      }
      geoApplied = true;
      const hit = CITY_LIST.find(c => c.n.toLowerCase() === g.city.toLowerCase());
      if (hit) pickCity(hit);
      else { activeCity = g.city; setCityView(g.city, g.lat, g.lng); }
      loadWeather();
    }

    // === Реальная база станций с прода: ближайшие к выбранной точке ===
    let STATIONS_DB = null;
    let weatherDone = false;
    let introMode = true;

    function enterIntro() {
      if (!userPos || !introMode) return;
      introMode = true;
      try {
        rangeCircle.setRadius(2000);
        isoLabel.setLatLng(userPos);
        isoLabel.setIcon(L.divIcon({ className: 'iso-label', html: '<span>2 км · стартовая зона</span>', iconSize: [0, 0], iconAnchor: [0, 0] }));
        map.flyToBounds(L.latLngBounds([userPos[0] - 0.09, userPos[1] - 0.144], [userPos[0] + 0.09, userPos[1] + 0.144]), { duration: 0.8 });
        showToast('Стартовая зона 2 км');
      } catch (e) {}
    }

    function exitIntro() {
      if (!introMode) return;
      introMode = false;
      try {
        isoLabel.setLatLng(userPos);
        recalc(true);
      } catch (e) {}
    }

    function haversine(a, b) {
      const R = 6371, dLat = (b[0] - a[0]) * Math.PI / 180, dLon = (b[1] - a[1]) * Math.PI / 180;
      const x = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * Math.PI / 180) * Math.cos(b[0] * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
      return 2 * R * Math.asin(Math.sqrt(x));
    }

    function fmtT80(pw) {
      const mins = Math.round(64 / (pw * 0.8) * 60);
      if (!isFinite(mins) || mins <= 0) return '—';
      if (mins < 60) return '~' + mins + ' мин';
      return '~' + Math.floor(mins / 60) + ' ч ' + (mins % 60 ? (mins % 60) + ' мин' : '');
    }

    function portLabel(arr) {
      if (!arr || !arr.length) return '—';
      return arr.map(p => p === 'type2' ? 'Type 2' : p).slice(0, 2).join(' + ');
    }

    async function loadStationDB() {
      try {
        const r = await fetch('/charging/stations.json', { cache: 'no-cache' });
        if (!r.ok) return;
        const d = await r.json();
        STATIONS_DB = d.stations || [];
        renderNearby();
        renderAllStations();
        loadOsmIndex();
      } catch (e) {}
    }

    function loadOsmIndex() {
      fetch('/charging/osm-full.json').then(r => r.ok ? r.json() : null).then(d => {
        if (!d || !d.stations || !d.stations.length) return;
        const have = new Set(STATIONS_DB.map(x => (x.src || 'base') + '|' + x.lat.toFixed(4) + '|' + x.lon.toFixed(4)));
        let add = 0;
        d.stations.forEach(s => {
          const k = (s.src || 'base') + '|' + s.lat.toFixed(4) + '|' + s.lon.toFixed(4);
          if (have.has(k)) return;
          have.add(k);
          STATIONS_DB.push(s);
          add++;
        });
        if (!add) return;
        renderAllStations();
      }).catch(() => {});
    }

    let stCluster = null;
    let baseMode = 'all';
    let OSM_FULL = null;
    let osmLoading = false;

    function renderAllStations() {
      if (!STATIONS_DB || !STATIONS_DB.length || typeof L.markerClusterGroup !== 'function') return;
      if (stCluster) { map.removeLayer(stCluster); stCluster = null; }
      stCluster = L.markerClusterGroup({ chunkedLoading: true, showCoverageOnHover: false, maxClusterRadius: 64, disableClusteringAtZoom: 14 });
      const pts = [];
      const srcList = (baseMode === 'osm') ? (OSM_FULL || []) : STATIONS_DB.concat(((baseMode === 'all' && OSM_FULL) ? OSM_FULL : []));
      srcList.forEach((x) => {
        if (typeof x.lat !== 'number' || typeof x.lon !== 'number') return;
        if (baseMode === 'base' && (x.src === 'yandex' || x.src === 'osm')) return;
        if (baseMode === 'yandex' && x.src !== 'yandex') return;
        if (baseMode === 'osm' && x.src !== 'osm') return;
        const pw = Number(x.pw) || 0;
        const isYa = x.src === 'yandex';
        const st = L.circleMarker([x.lat, x.lon], {
          radius: pw >= 50 ? 6.5 : 5.5,
          color: isYa ? '#3FA9F5' : '#E85002',
          weight: 34,
          opacity: 0,
          fillColor: isYa ? '#3FA9F5' : '#E85002',
          fillOpacity: (pw >= 50 || isYa) ? 0.95 : 0.7
        });
        st.bindPopup('<div class="st-pop">'
          + '<div class="st-pop-name">' + (x.op || x.n || 'ЭЗС') + (x.src === 'yandex' ? ' · Я' : '') + '</div>'
          + '<div class="st-pop-addr">' + (x.a || '') + '</div>'
          + '<div class="st-pop-grid"><div><span>Мощность</span><b>' + kwLabel(pw) + '</b></div><div><span>Порты</span><b>' + (x.s && x.s.length ? x.s.join(', ') : '—') + '</b></div></div>'
          + '<a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=' + encodeURIComponent(userPos[0] + ',' + userPos[1] + '~' + x.lat + ',' + x.lon) + '&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>'
          + '</div>', { maxWidth: 250 });
        pts.push(st);
      });
      stCluster.addLayers(pts);
      map.addLayer(stCluster);
      const sw = document.getElementById('baseSwitch');
      if (sw) {
        const nb = STATIONS_DB.filter(x => x.src === 'yandex').length;
        const no = STATIONS_DB.filter(x => x.src === 'osm').length;
        const q = (sel, txt) => { const el = sw.querySelector(sel); if (el) el.textContent = txt; };
        q('[data-mode=all]', 'Всё · ' + (STATIONS_DB.length + (OSM_FULL ? OSM_FULL.length : 0)).toLocaleString('ru-RU'));
        q('[data-mode=base]', 'Наши · ' + (STATIONS_DB.length - nb - no).toLocaleString('ru-RU'));
        q('[data-mode=yandex]', 'Яндекс · ' + nb.toLocaleString('ru-RU'));
        q('[data-mode=osm]', 'OSM · ' + ((OSM_FULL && OSM_FULL.length) || no).toLocaleString('ru-RU'));
      }
      showToast('Все ' + pts.length.toLocaleString('ru-RU') + ' станций на карте');
    }

    function setBaseMode(m) {
      baseMode = m;
      if (m === 'osm' && !OSM_FULL && !osmLoading) {
        osmLoading = true;
        fetch('/charging/osm-full.json', { cache: 'no-store' }).then(r => r.json()).then(d => { OSM_FULL = (d && d.stations) || []; osmLoading = false; renderAllStations(); }).catch(() => { osmLoading = false; showToast('Полная OSM-база пока недоступна'); });
      }
      document.querySelectorAll('.base-switch button').forEach(b => b.classList.toggle('active', b.dataset.mode === m));
      renderAllStations();
      const nb = STATIONS_DB.filter(x => x.src === 'yandex').length;
      const label = m === 'yandex' ? ('Яндекс · ' + nb) : m === 'base' ? ('Наша база · ' + (STATIONS_DB.length - nb)) : m === 'osm' ? ('OSM · ' + ((OSM_FULL && OSM_FULL.length) || 0)) : ('Все базы · ' + (STATIONS_DB.length + (OSM_FULL ? OSM_FULL.length : 0)));
      showToast('На карте: ' + label);
    }

    function renderNearby() {
      if (!STATIONS_DB || !STATIONS_DB.length) return;
      const near = STATIONS_DB
        .map(x => ({ x: x, d: haversine(userPos, [x.lat, x.lon]) }))
        .filter(v => v.d <= 30)
        .sort((a, b) => a.d - b.d)
        .slice(0, 10)
        .map(v => ({
          name: (v.x.op || v.x.n || 'ЭЗС') + (v.x.src === 'ya' ? ' · Я' : ''),
          addr: v.x.a || '',
          km: Math.max(0.1, Math.round(v.d * 10) / 10),
          type: (v.x.pw || 0) >= 50 ? 'dc' : (v.x.pw ? 'ac' : 'na'),
          label: v.x.pw ? String(v.x.pw) : '—',
          kw: v.x.pw,
          port: portLabel(v.x.s),
          t80: v.x.pw ? fmtT80(v.x.pw) : '—',
          tariff: '',
          coords: [v.x.lat, v.x.lon]
        }));
      if (!near.length) return;
      stations = near;
      addStationMarkers();
      renderCards();
      renderTable();
    }

    function tempNow() {
      const part = document.getElementById('weatherBadge').textContent.split('·')[0].trim();
      return /\d/.test(part) ? part : '+20°C';
    }

    function toggleReturn() {
      state.roundTrip = !state.roundTrip;
      const btn = document.getElementById('returnToggle');
      if (btn) btn.classList.toggle('active', state.roundTrip);
      recalc(true);
      showToast(state.roundTrip ? 'Возврат учтён: зона доезда и обратно' : 'Возврат отключён: только до станции');
    }

    function openShare() {
      const km = document.getElementById('kmDisplay').textContent;
      const soc = document.getElementById('socSlider').value;
      const model = document.getElementById('carModelTitle').textContent.split('·')[0].trim();
      const t = tempNow();
      document.getElementById('shareTitle').textContent = model + ' в ' + t;
      document.getElementById('shareKm').textContent = km + ' км';
      document.getElementById('shareNote').textContent = 'реальный пробег при ' + t + ' и заряде ' + soc + '%' + (state.roundTrip ? ' (туда-обратно)' : '');
      document.getElementById('shareModal').classList.add('show');
    }

    function closeShare() {
      document.getElementById('shareModal').classList.remove('show');
    }

    function copyShare() {
      const text = 'Запас хода EV — ' + document.getElementById('shareTitle').textContent + ': ' + document.getElementById('shareKm').textContent + ' (' + document.getElementById('shareNote').textContent + ') → zapashoda-ev.ru/dashboard/';
      if (navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
      showToast('Текст скопирован');
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

    // pickCity и pickCityChip объявлены ниже (единая setCityView)

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

    // renderModels объявлен выше (полный каталог 154)

    // openCarModal объявлен выше (полный каталог 154)

    function closeCarModal() {
      document.getElementById('carModal').classList.remove('open');
    }

    // filterModels объявлен выше (фаззи-поиск с транслитерацией)

    function chooseModel(name, base, port, direct, est) {
      state.baseKm = base;
      document.getElementById('carModelTitle').textContent = name;
      document.getElementById('carPortTag').textContent = port || '—';
      document.getElementById('carBaseKm').textContent = est ? '≈ ' + base + ' км (оценка по ёмкости)' : 'Паспортный запас: ' + base + ' км';
      document.getElementById('compatText').textContent = direct ? 'Напрямую DC' : 'Через адаптер';
      updateChart(base);
      closeCarModal();
      recalc(true);
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
      showToast('Открываем маршрут в Яндекс.Картах');
      window.open(url, '_blank');
    }

    // === Тарифы из источников (site/public/tariffs.json, обновляется Actions) ===
    let TARIFFS = null;

    function tariffFor(s) {
      if (!TARIFFS || !TARIFFS.networks) return null;
      const name = s.name || '';
      for (const [net, t] of Object.entries(TARIFFS.networks)) {
        if (name.includes(net)) {
          const v = s.type === 'ac' ? t.ac : t.dc;
          return (v != null) ? (v + ' ₽/кВт·ч') : null;
        }
      }
      return null;
    }

    function tariffLabel(s) {
      const v = tariffFor(s);
      if (v) return v;
      if (TARIFFS && TARIFFS.market && TARIFFS.market.dc_typical) {
        return 'от ' + TARIFFS.market.dc_typical[0] + ' ₽/кВт·ч';
      }
      return s.tariff;
    }

    function tariffStampHtml() {
      if (!TARIFFS) return '';
      const d = (TARIFFS.updated || '').slice(0, 10).split('-').reverse().join('.');
      const failed = Object.values(TARIFFS.networks || {}).some(t => t.status === 'parse_failed');
      return '<div style="font-size:10px;color:var(--text-dim);padding:0 4px 10px;font-variant-numeric:tabular-nums;">Тарифы сетей · обновлено ' + d + (failed ? ' · часть источников недоступна' : '') + '</div>';
    }

    async function loadTariffs() {
      try {
        const r = await fetch('/tariffs.json', { cache: 'no-cache' });
        if (!r.ok) return;
        TARIFFS = await r.json();
        renderCards();
        renderTable();
      } catch (e) { /* молча: остаётся прежний тариф */ }
    }

    function renderCards() {
      document.getElementById('rightDrawer').innerHTML = tariffStampHtml() + stations.map((s, i) => `
        <div class="station-item ${i === 0 ? 'selected' : ''}" id="stCard${i}" onclick="focusStation(${i})">
          <div class="st-top">
            <div style="min-width: 0;">
              <div class="st-name">${s.name}</div>
              <div class="st-addr">${s.addr} · ${s.km} км</div>
            </div>
            <div class="st-kw" style="color: ${typeColor(s.type)};">${kwLabel(s.kw)}</div>
          </div>
          <div class="st-metrics">
            <div>
              <div class="st-m-label">Разъем</div>
              <div class="st-m-val" style="color: ${typeColor(s.type)};">${s.port}</div>
            </div>
            <div>
              <div class="st-m-label">До 80%</div>
              <div class="st-m-val">${s.t80}</div>
            </div>
            <div>
              <div class="st-m-label">Тариф</div>
              <div class="st-m-val"${s.type === 'ac' ? '' : ''}>${tariffLabel(s)}</div>
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
          <div class="r-col">Тариф<b>${tariffLabel(s)}</b></div>
          <span class="st-kw-mini" style="color: ${typeColor(s.type)}; background: ${typeBg(s.type)};">${kwLabel(s.kw)}</span>
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
    loadTariffs();
    loadModelsCatalog();
    loadStationDB();
    loadGeoCity();
    document.getElementById('cityInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); citySearch(); }
    });
    document.getElementById('cityInput').addEventListener('change', citySearch);

    // Свайп по хендлу шита: вверх — развернуть, вниз — свернуть
    const sheetEl = document.querySelector('.hud-left');
    const sheetHandle = document.querySelector('.stack-handle');
    let sheetTouchY = null;
    sheetHandle.addEventListener('touchstart', (e) => { sheetTouchY = e.touches[0].clientY; }, { passive: true });
    sheetHandle.addEventListener('touchend', (e) => {
      if (sheetTouchY == null) return;
      const dy = e.changedTouches[0].clientY - sheetTouchY;
      if (dy > 36) sheetEl.classList.remove('open');
      else if (dy < -36) sheetEl.classList.add('open');
      sheetTouchY = null;
    }, { passive: true });
  