var ZH_BUILD = 1867;

    // Подложка: Esri Dark Gray — реальные тайлы на всех зумах (CARTO из РФ отдаёт заглушки на глубоких зумах).
    // Страховка: 4 ошибки подряд — авто-переход на резервный источник.
    const map = L.map('map', { zoomControl: false, keepBuffer: 1, updateWhenZooming: false, preferCanvas: true }).setView([55.775, 37.56], 12);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      maxNativeZoom: 19,
      updateWhenIdle: true
    }).addTo(map);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      maxNativeZoom: 19,
      opacity: 0.85,
      updateWhenIdle: true
    }).addTo(map);
    let _tileErrCount = 0, _tileFallbackDone = false;
    map.on('tileerror', () => {
      if (_tileFallbackDone) return;
      if (++_tileErrCount >= 4) {
        _tileFallbackDone = true;
        map.eachLayer(l => {
          if (l instanceof L.TileLayer) map.removeLayer(l);
        });
        if (!document.getElementById('zh-osm-dark')) { const st = document.createElement('style'); st.id = 'zh-osm-dark'; st.textContent = '.zh-osm-dark{filter:grayscale(1) invert(1) brightness(.92) contrast(.92)}'; document.head.appendChild(st); }
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, subdomains: 'abc', className: 'zh-osm-dark', updateWhenIdle: true }).addTo(map);
        showToast('Подложка карты переключена на резервный источник');
      }
    });

    

    // Изохрона реального пробега вокруг машины
    let userPos = [55.785, 37.535]; let userPosGeo = true;
    updateBarGeo();
    const rangeCircle = L.circle(userPos, {
      color: '#E85002',
      weight: 1.5,
      dashArray: '8, 12',
      className: 'zh-iso',
      fillOpacity: 0,
      radius: 4320
    }).addTo(map);
    // Затемнение СНАРУЖИ зоны доезда (внутри кольца — чистая карта), панель под маркерами
    const shadePane = map.createPane('zhShade'); shadePane.style.zIndex = 350; shadePane.style.pointerEvents = 'none';
    const shadeLayer = L.polygon([], { fillColor: '#050507', fillOpacity: 0.2, stroke: false, interactive: false, pane: 'zhShade' }).addTo(map);
    function updateShade() {
      try {
        const c = rangeCircle.getLatLng(), r = rangeCircle.getRadius();
        if (!c || !r) { shadeLayer.setLatLngs([]); return; }
        const pts = [];
        for (let i = 0; i <= 64; i++) {
          const a = i / 64 * 2 * Math.PI;
          pts.push([c.lat + (r / 111320) * Math.cos(a), c.lng + (r / (111320 * Math.cos(c.lat * Math.PI / 180) || 1)) * Math.sin(a)]);
        }
        const big = [[c.lat - 8, c.lng - 14], [c.lat - 8, c.lng + 14], [c.lat + 8, c.lng + 14], [c.lat + 8, c.lng - 14]];
        shadeLayer.setLatLngs([big, pts]);
      } catch (e) {}
    }
    updateShade();
    const _rcSL = rangeCircle.setLatLng.bind(rangeCircle);
    rangeCircle.setLatLng = function (ll) { const v = _rcSL(ll); updateShade(); return v; };
    const _rcSR = rangeCircle.setRadius.bind(rangeCircle);
    rangeCircle.setRadius = function (r) { const v = _rcSR(r); updateShade(); return v; };

    // Подпись зоны доезда у метки машины (видна всегда, даже когда кольцо больше экрана)
    const isoLabel = L.marker(userPos, {
      icon: L.divIcon({ className: 'iso-label', html: '<span>432 км · запас хода</span>', iconSize: [0, 0], iconAnchor: [0, 0] }),
      interactive: false
    }).addTo(map);

    function updateIsoLabel(km) {
      isoLabel.setLatLng(userPos);
      isoLabel.setIcon(L.divIcon({ className: 'iso-label', html: '<span>' + km + ' км · запас хода</span>', iconSize: [0, 0], iconAnchor: [0, 0] }));
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
            L.popup().setLatLng([best.lat, best.lon]).setContent(function () { return buildRichPopup(best); }).openOn(map);
            return;
          }
        } catch (err) {}
      }
      if (introMode) introMode = false;
      userPos = [e.latlng.lat, e.latlng.lng]; userPosGeo = false;
      rangeCircle.setLatLng(userPos);
      if (typeof meMarker !== 'undefined') meMarker.setLatLng(userPos);
      if (typeof isoLabel !== 'undefined') isoLabel.setLatLng(userPos);
      recalc(false);
      showToast('Точка установлена · маршрут — тап по станции → «Маршрут от меня»');
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
        try { if (st.type === 'na') { const g = m.getElement && m.getElement(); if (g) g.style.pointerEvents = 'none'; } } catch (e) {}
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
          <a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=${encodeURIComponent((userPosGeo ? '~' : userPos[0] + ',' + userPos[1] + '~') + st.coords[0] + ',' + st.coords[1])}&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>
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
    const meMarker = L.marker(userPos, { icon: meIcon, interactive: true, draggable: true, keyboard: false, zIndexOffset: 500 }).addTo(map);
    meMarker.on('dragend', function () {
      try {
        const p = meMarker.getLatLng();
        userPos = [p.lat, p.lng]; userPosGeo = false;
        rangeCircle.setLatLng(userPos);
        if (typeof isoLabel !== 'undefined') isoLabel.setLatLng(userPos);
        recalc(false);
        showToast('Точка переставлена');
      } catch (e) {}
    });

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
          const _ck = document.getElementById('carLiveKm');
          if (_ck) _ck.textContent = km.toLocaleString('ru-RU') + ' км';
          const _cp = document.getElementById('carLivePct');
          if (_cp) _cp.textContent = soc + '% заряда';
          return;
        }
      }
      const soc = parseInt(document.getElementById('socSlider').value, 10);
      const km = Math.round(state.baseKm * (soc / 100) * state.mult * (state.roundTrip ? 0.5 : 1));
      document.getElementById('kmDisplay').textContent = km;
      document.getElementById('pctDisplay').textContent = soc + '%';
      const _ck = document.getElementById('carLiveKm');
      if (_ck) _ck.textContent = km.toLocaleString('ru-RU') + ' км';
      const _cp = document.getElementById('carLivePct');
      if (_cp) _cp.textContent = soc + '% заряда';
      const _t = (typeof state.temp === 'number') ? state.temp : null;
      document.getElementById('heroFormula').textContent = 'При заряде ' + soc + '%' + (_t === null ? '' : ' и ' + (_t > 0 ? '+' + _t : _t) + '° за окном') + ' проедете ≈ ' + km + ' км' + (state.roundTrip ? ' (туда-обратно)' : '');
      rangeCircle.setRadius(km * 1000);
      updateIsoLabel(km);
      // Авто-подгонка обзора — только по крупным событиям (точка кривой, сценарий, модель, погода).
      // При движении слайдера карту НЕ дёргаем: это давало непрерывную перерисовку и тормоза.
      if (fit) scheduleFit();
      updateWinterBox();
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

    function nearestChartIdx(t) {
      let best = 0, bd = 1e9;
      CHART_TEMPS.forEach(function (s, i) {
        var v = parseFloat(String(s).replace('−', '-').replace('+', ''));
        var d = Math.abs(v - t);
        if (d < bd) { bd = d; best = i; }
      });
      return best;
    }
    function catOf(x) {
      if (x.src === 'yandex') return 'ya';
      var s = ((x.s || []).join(' ') || '').toLowerCase();
      var pw = Number(x.pw) || 0;
      if (x.u || !s) return 'unv';
      if (s.indexOf('gb_dc') >= 0 || (s.indexOf('gb/t') >= 0 && pw >= 50)) return 'dc';
      if (s.indexOf('ccs') >= 0 || s.indexOf('type2_combo') >= 0) return 'adp';
      return 'ac';
    }
    function legName(cat) {
      return { dc: 'Быстрая DC (напрямую)', adp: 'Через переходник (CCS2)', ac: 'Медленная AC', unv: 'Не проверено', ya: 'Точка Яндекса' }[cat] || cat;
    }
    function countCat(cat) {
      var c = 0;
      var src = (baseMode === 'osm') ? (OSM_FULL || []) : STATIONS_DB.concat(((baseMode === 'all' && OSM_FULL) ? OSM_FULL : []));
      src.forEach(function (x) { if (catOf(x) === cat) c++; });
      return c;
    }
    function legClick(cat) {
      mapFilterCat = (mapFilterCat === cat) ? null : cat;
      document.querySelectorAll('.leg-chip').forEach(function (b) { b.classList.toggle('active', b.dataset.f === mapFilterCat || (!mapFilterCat && b.dataset.f === 'all')); });
      renderAllStations();
      if (mapFilterCat) {
        var n = countCat(cat);
        var w = (n % 10 === 1 && n % 100 !== 11) ? 'точка' : ((n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) ? 'точки' : 'точек');
        showToast('Показаны: ' + legName(cat) + ' — ' + n + ' ' + w);
      } else { showToast('Фильтр снят — вся база'); }
    }
    function legAll() {
      mapFilterCat = null;
      document.querySelectorAll('.leg-chip').forEach(function (b) { b.classList.toggle('active', b.dataset.f === 'all'); });
      renderAllStations();
      showToast('Вся база — ' + (STATIONS_DB ? STATIONS_DB.length : 0) + ' точек');
    }
    var zhTipTimer = null;
    function zhHelpToggle(e) {
      var tip = document.getElementById('zhHelpTip');
      if (!tip) return;
      if (e) e.stopPropagation();
      tip.classList.toggle('open');
      if (zhTipTimer) { clearTimeout(zhTipTimer); zhTipTimer = null; }
      if (tip.classList.contains('open')) { zhTipTimer = setTimeout(function(){ tip.classList.remove('open'); }, 6000); }
    }
    document.addEventListener('click', function (e) {
      var tip = document.getElementById('zhHelpTip');
      if (tip && tip.classList.contains('open') && !(e.target.closest && e.target.closest('.zh-help'))) tip.classList.remove('open');
    });

    function setScenario(el, m, temp, icon, desc, impact, idx) {
      state.scenMult = m;
      state.mult = ((state.tempPct !== undefined && state.tempPct !== null) ? state.tempPct : 1) * m;
      document.querySelectorAll('.scen-btn').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      const rt = (typeof state.temp === 'number') ? ((state.temp > 0 ? '+' + state.temp : state.temp) + '°') : temp;
      document.getElementById('weatherTemp').textContent = rt;
      document.getElementById('weatherIcon').innerHTML = (typeof state.temp === 'number' && state.temp <= 0) ? WICON.snow : (WICON[icon] || '');
      document.getElementById('weatherCity').textContent = state.city + ' · ' + desc;
      document.getElementById('impactBadge').textContent = impact;
      document.getElementById('weatherBadge').textContent = el.textContent + ' · ' + rt;
      let ci = (typeof chartActive === 'number') ? chartActive : idx;
      if (m === .72) ci = 0;
      else if (m === .88) ci = 5;
      else if (m === 1) { if (typeof state.temp === 'number') ci = nearestChartIdx(state.temp); }
      setChartActive(ci);
      recalc(true);
    }



    function switchDb(mode) {
      const yandex = mode === 'yandex';
      document.getElementById('tabOurBase').classList.toggle('active', !yandex);
      var _ty = document.getElementById('tabYandex'); if (_ty) _ty.classList.toggle('active', yandex);
      // Яндекс-слой накладывается поверх нашей базы, а не заменяет ее
      if (yandex) yanLayer.addTo(map); else map.removeLayer(yanLayer);
      const fa = document.getElementById('filterArea');
      if (fa) fa.style.opacity = yandex ? '0.45' : '1';
      var _yn = document.getElementById('yandexNote'); if (_yn) _yn.style.display = yandex ? 'block' : 'none';
      showToast(yandex ? 'Слой Яндекс.Карт наложен на нашу карту' : 'Показана только наша база');
      try { updateChipCounts(); } catch (e) {}
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
            + '<a class="st-pop-btn" href="https://yandex.ru/maps/?rtext=' + encodeURIComponent((userPosGeo ? '~' : userPos[0] + ',' + userPos[1] + '~') + s.coords[0] + ',' + s.coords[1]) + '&rtt=auto" target="_blank" rel="noopener">Маршрут в Яндекс.Карты</a>'
            + '</div>').openOn(map);
        } catch (e) {}
      }, 950);
    }

    function locateUser() {
      map.flyTo(userPos, 13);
    }

    // === Полный каталог моделей с прода (154) + умный поиск ===
    let MODELS_ALL = null;

    function restoreCar() {
      try {
        const raw = localStorage.getItem('zh-car');
        if (!raw) return;
        const c = JSON.parse(raw);
        if (!c || !c.name) return;
        window.__zhModelSlug = null;
        chooseModel(c.name, c.base, c.port, c.direct, c.est);
        const mm = (MODELS_ALL || []).find(m => m.name === c.name);
        window.__zhModelSlug = mm ? mm.slug : null;
        if (c.base != null) { introMode = false; recalc(false); }
        updateWinterBox();
      } catch (e) {}
    }

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
        restoreCar();
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
          : 'Паспортный запас не указан — расчёт по последней выбранной модели';
        const escN = (m.name || '').replace(/'/g, "\\'"), escP = (m.port || '').replace(/'/g, "\\'");
        const click = `chooseModelModel('${escN}', ${base || 'null'}, '${escP}', ${m.d ? 'true' : 'false'}, ${m.est ? 'true' : 'false'})`;
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
      try { const mm = (MODELS_ALL || []).find(m => m.name === name); window.__zhModelSlug = mm ? mm.slug : null; } catch (e) {}
      chooseModel(name, base, port, direct, est);
    }

    function openCarModal() {
      filterModels('');
      document.getElementById('carModal').classList.add('open');
    }

    // === Погода по гео: open-meteo ===
    // fetch с таймаутом: зависший внешний API больше не блокирует бейдж погоды
    function fetchTO(url, opts, ms) {
      const c = (typeof AbortController !== 'undefined') ? new AbortController() : null;
      const id = c ? setTimeout(() => c.abort(), ms || 6000) : null;
      const p = fetch(url, (opts && c) ? Object.assign({}, opts, { signal: c.signal }) : opts);
      return p.finally(() => { if (id) clearTimeout(id); });
    }
    async function loadWeather() {
      if (weatherDone) return;
      const noGeo = !userPos;
      const refCity = noGeo ? (CITY_LIST.find(c => c.n === state.city) || CITY_LIST[0]) : null;
      const wLat = noGeo ? refCity.lat : userPos[0];
      const wLon = noGeo ? refCity.lng : userPos[1];
      if (noGeo) showToast('Не определили ваш город — погода по «' + (refCity ? refCity.n : 'Москве') + '»');
      try {
        const cached = JSON.parse(localStorage.getItem('zh-weather-dash') || 'null');
        if (cached && cached.city === state.city && typeof cached.t === 'number' && Date.now() - cached.ts < 30 * 60 * 1000) {
          weatherDone = true;
          applyWeatherTemp(cached.t, 'кэш');
          return;
        }
      } catch (e) {}
      try {
        const r = await fetchTO('https://api.open-meteo.com/v1/forecast?latitude=' + wLat.toFixed(3) + '&longitude=' + wLon.toFixed(3) + '&current=temperature_2m', { cache: 'no-store' }, 6000);
        const d = r ? await r.json() : null;
        const t = d && d.current && typeof d.current.temperature_2m === 'number' ? Math.round(d.current.temperature_2m) : null;
        if (t !== null) { weatherDone = true; saveWeatherCache(t); applyWeatherTemp(t, 'open-meteo'); return; }
      } catch (e) {}
      try {
        const r2 = await fetchTO('https://wttr.in/' + wLon.toFixed(2) + ',' + wLat.toFixed(2) + '?format=j1', { cache: 'no-store' }, 6000);
        const d2 = r2 ? await r2.json() : null;
        const tc = d2 && d2.current_condition && d2.current_condition[0] ? parseInt(d2.current_condition[0].temp_C, 10) : null;
        if (tc !== null && !isNaN(tc)) { weatherDone = true; saveWeatherCache(tc); applyWeatherTemp(tc, 'wttr.in'); return; }
      } catch (e) {}
      try {
        const r3 = await fetchTO('/charging/weather.json', { cache: 'no-cache' }, 6000);
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
        const wts = hit && hit.ts ? Date.parse(hit.ts) : 0;
        const fresh = wts && (Date.now() - wts) < 48 * 3600 * 1000;
        const ageH = wts ? Math.round((Date.now() - wts) / 3600000) : 999;
        if (hit && typeof hit.t === 'number' && fresh) {
          weatherDone = true;
          applyWeatherTemp(Math.round(hit.t), (bestD < 1e8 ? bestName : 'резерв') + ' · ' + ageH + ' ч назад');
          return;
        }
      } catch (e) {}
      const nav = (navigator.onLine === false) ? 'нет сети' : 'сеть есть';
      const reason = (navigator.onLine === false) ? 'нет сети' : 'сервисы погоды не ответили';
      try { localStorage.setItem('zh-wx-diag', JSON.stringify({ at: new Date().toISOString(), online: navigator.onLine, ua: navigator.userAgent.slice(0, 60), d: navigator.userAgent.includes('Mobi') })); } catch (e) {}
      showToast('Погода недоступна (' + reason + ') — тап по бейджу погоды — повторим');
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
    async function pwaRefresh() {
      try {
        if ('caches' in window) { const ks = await caches.keys(); await Promise.all(ks.map(k => caches.delete(k))); }
        if ('serviceWorker' in navigator) { const rs = await navigator.serviceWorker.getRegistrations(); rs.forEach(r => { try { r.update(); } catch (e) {} }); }
        try { localStorage.setItem('zh-pwa-refresh', String(Date.now())); } catch (e) {}
        showToast('Обновляем приложение…');
        setTimeout(() => location.replace(location.href.split('#')[0]), 700);
      } catch (e) { showToast('Не удалось обновить: ' + e.message); }
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
      state.tempPct = pct / 100;
      state.mult = state.tempPct * (state.scenMult || 1);
      const lbl = t > 0 ? '+' + t : String(t);
      state.temp = t;
      const w3t = document.getElementById('weatherTemp');
      if (w3t) w3t.textContent = lbl + '°';
      const w3c = document.getElementById('weatherCity');
      if (w3c) w3c.textContent = displayCity() + ' · живой прогноз';
      const wi = document.getElementById('weatherIcon');
      if (wi) wi.innerHTML = t <= 0 ? WICON.snow : WICON.sun;
      document.getElementById('weatherBadge').textContent = lbl + '° · погода';
      const bw = document.getElementById('barWeatherChip');
      if (bw) { bw.style.display = 'inline-flex'; const bt = document.getElementById('barTemp'); if (bt) bt.textContent = lbl + '°'; const bi = document.getElementById('barWIcon'); if (bi) bi.innerHTML = t <= 0 ? WICON.snow : WICON.sun; }
      const ib = document.getElementById('impactBadge');
      const eff = Math.round(state.mult * 100);
      if (ib) ib.textContent = (eff < 100 ? '−' + (100 - eff) : '100') + '% от нормы';
      setChartActive(idx);
      recalc(false);
      updateWinterBox();
      const gt = document.getElementById('barGeoText');
      if (gt) gt.textContent = geoShort(displayCity());
      // тост погоды убран: чип «город · °C» уже живёт в шапке
    }

    function geoShort(n){try{if(innerWidth<=820 || innerHeight<=560){var G={'Москва':'МСК','Санкт-Петербург':'СПб','Новосибирск':'НСК','Екатеринбург':'ЕКБ','Нижний Новгород':'НН','Казань':'КЗН','Челябинск':'ЧЛБ','Красноярск':'КРС','Самара':'СМР','Ростов-на-Дону':'РНД','Краснодар':'КРД','Омск':'ОМС','Пермь':'ПРМ','Воронеж':'ВРН','Волгоград':'ВЛГ','Саратов':'СРТ','Тюмень':'ТЮМ','Тольятти':'ТЛТ','Ижевск':'ИЖВ','Барнаул':'БРН','Ульяновск':'УЛН','Иркутск':'ИРК','Хабаровск':'ХБР','Ярославль':'ЯРЛ','Владивосток':'ВЛД','Махачкала':'МХЧ','Томск':'ТМК','Оренбург':'ОРБ','Кемерово':'КМР','Новокузнецк':'НКЗ','Рязань':'РЯЗ','Астрахань':'АСТ','Набережные Челны':'НЧЛ','Пенза':'ПНЗ','Липецк':'ЛПЦ','Киров':'КРВ','Чебоксары':'ЧБК','Тула':'ТУЛ','Калининград':'КЛГ','Курск':'КРК','Ставрополь':'СТВ','Сочи':'СЧИ','Белгород':'БЛГ','Сургут':'СРГ','Владимир':'ВЛМ','Архангельск':'АРХ','Тверь':'ТВР','Брянск':'БРЯ'};if(G[n])return G[n];if(n&&n.length>6)return n.slice(0,3).toUpperCase()}}catch(e){}return n}      function updateBarGeo(){try{const gt=document.getElementById('barGeoText');if(gt)gt.textContent=geoShort(displayCity());}catch(e){}}      function updateChipCounts(){try{['dc','adp','ac','unv','ya'].forEach(function(c){var el=document.querySelector('.leg-chip[data-f="'+c+'"] .cnt');if(el)el.textContent=countCat(c);});}catch(e){}}

    function driveOn(){
      document.body.classList.add('drive');
      try{document.querySelectorAll('.zh-ask').forEach(x=>x.style.display='none');}catch(e){}
      try{introMode=false;}catch(e){}
      try{history.replaceState(null,'',location.pathname+'?mode=drive');}catch(e){}
      const t=document.getElementById('driveToggle');
      if(t) t.textContent='Выйти из режима за рулём';
      closeSideMenu();
      showToast('Режим за рулём: карта на весь экран, одна кнопка — ближайшая ЭЗС');
    }
    function driveOff(){
      document.body.classList.remove('drive');
      try{history.replaceState(null,'',location.pathname);}catch(e){}
      const t=document.getElementById('driveToggle');
      if(t) t.textContent='Режим за рулём';
      showToast('Режим за рулём выключен');
    }
    function toggleDrive(){ document.body.classList.contains('drive') ? driveOff() : driveOn(); }
    function driveNearest(){
      if(!STATIONS_DB || !STATIONS_DB.length){ showToast('База ещё загружается — секунду'); return; }
      const go = (pos) => {
        if(!pos){ showToast('Точка не определена'); return; }
        let best=null,bd=1e9;
        STATIONS_DB.forEach(x=>{ try{ const d=haversine(pos,[x.lat,x.lon]); if(d<bd){bd=d;best=x;} }catch(e){} });
        if(!best){ showToast('Станций не найдено'); return; }
        try{ map.flyTo([best.lat,best.lon], 15); }catch(e){}
        buildRoute(best.lat,best.lon);
        showToast('Маршрут до ближайшей ЭЗС · '+bd.toFixed(1)+' км');
      };
      if(navigator.geolocation && navigator.geolocation.getCurrentPosition){
        showToast('Определяю ваше место…');
        navigator.geolocation.getCurrentPosition(
          p => go([p.coords.latitude, p.coords.longitude]),
          () => go(userPos),
          { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
        );
      } else { go(userPos); }
    }
    try{ if(new URLSearchParams(location.search).get('mode')==='drive'){ document.body.classList.add('drive'); } }catch(e){}

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
        renderNearby();
        switchView('list');
        setActiveTab('tabStationsM');
      } else if (view === 'car') {
        const hud = document.querySelector('.hud-left');
        const wasOpen = hud.classList.contains('open');
        if (wasOpen) { hud.classList.remove('open'); setActiveTab('tabMapM'); switchView('map'); }
        else { switchView('map'); hud.classList.add('open'); setActiveTab('tabCarM'); }
      }
    }

    // Тап по кластеру: DOM-обработчик (нативный Leaflet на тач-экранах клик по кластеру теряет)
    let _clTapTs = 0;
    document.addEventListener('click', function (e) {
      const el = e.target && e.target.closest ? e.target.closest('.marker-cluster') : null;
      if (!el || Date.now() - _clTapTs < 600) return;
      _clTapTs = Date.now();
      try { e.stopPropagation(); } catch (err) {}
      openClusterModalAt(el);
    }, true);

    // Модал кластера: список станций + «Приблизить» (как на старой карте)
    function openClusterModalAt(el) {
      const r = el.getBoundingClientRect();
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      const ll = map.containerPointToLatLng(L.point(cx, cy));
      const declared = parseInt((el.textContent || '').replace(/[^\d]/g, ''), 10) || 0;
      const zoom = map.getZoom();
      const mpp = 156543.03392 * Math.cos(ll.lat * Math.PI / 180) / Math.pow(2, zoom); // метров на пиксель
      const radiusM = Math.max(64, 64) * mpp * 1.45;
      const items = [];
      const src = STATIONS_DB && STATIONS_DB.length ? STATIONS_DB : (OSM_FULL || []);
      for (let k = 0; k < src.length; k++) {
        const x = src[k];
        if (typeof x.lat !== 'number' || typeof x.lon !== 'number') continue;
        const dx = (x.lon - ll.lng) * Math.cos(ll.lat * Math.PI / 180) * 111320;
        const dy = (x.lat - ll.lat) * 110540;
        if (dx * dx + dy * dy <= radiusM * radiusM) items.push(x);
      }
      if (!items.length) {
        const z = Math.min(zoom + 2, 13);
        try { map.flyTo(ll, z, { animate: true }); } catch (e) { map.setView(ll, z); }
        return;
      }
      openClusterModalView(items, declared || items.length, ll);
    }
    // Модал кластера: список станций + «Приблизить» (как на старой карте)
    function openClusterModalView(items, declared, ll) {
      const n = declared || items.length;
      items.sort((a, b) => (Number(b.pw) || 0) - (Number(a.pw) || 0));
      window.__clItems = items;
      let ov = document.getElementById('clModal');
      if (!ov) {
        ov = document.createElement('div');
        ov.id = 'clModal';
        ov.className = 'cl-modal-overlay';
        ov.innerHTML = '<div class="cl-modal"><div class="cl-head"><div class="cl-title" id="clTitle">Кластер</div><button class="cl-close" onclick="closeClusterModal()" aria-label="Закрыть">✕</button></div><div class="cl-sub" id="clSub"></div><div class="cl-list" id="clList"></div><button class="cl-zoom" onclick="clusterZoom()">Приблизить карту</button></div>';
        document.body.appendChild(ov);
      }
      document.getElementById('clTitle').textContent = 'Кластер · ' + n;
      const sub = document.getElementById('clSub');
      const pws = items.map(x => Number(x.pw) || 0);
      const maxpw = pws.length ? Math.max(...pws) : 0;
      sub.textContent = (maxpw >= 50 ? 'До ' + maxpw + ' кВт' : 'Обычные станции') + ' · тап по станции — показать на карте';
      const list = document.getElementById('clList');
      list.innerHTML = items.slice(0, 15).map((x, i2) =>
        '<div class="cl-item" onclick="clusterItem(' + i2 + ')">' +
        '<div class="cl-item-main"><div class="cl-item-name">' + ((x.n || x.name || x.a || 'ЭЗС') + '').slice(0, 60) + '</div>' +
        '<div class="cl-item-meta">' + (x.pw ? x.pw + ' кВт' : 'мощность н/д') + ' · ' + ((x.a || x.addr || '').slice(0, 40)) + '</div></div>' +
        '<div class="cl-item-go">→</div></div>').join('') +
        (items.length > 15 ? '<div class="cl-more">и ещё ' + (items.length - 15) + ' станций в этом месте</div>' : '');
      ov.dataset.zoom = ll.lat + ',' + ll.lng;
      ov.style.display = 'flex';
    }
    function closeClusterModal() { const ov = document.getElementById('clModal'); if (ov) ov.style.display = 'none'; }
    function clusterZoom() {
      const ov = document.getElementById('clModal');
      if (!ov || !ov.dataset.zoom) return;
      const [la, ln] = ov.dataset.zoom.split(',').map(Number);
      closeClusterModal();
      const z = Math.min(map.getZoom() + 2, 13);
      try { map.flyTo([la, ln], z, { animate: true }); } catch (e) { map.setView([la, ln], z); }
    }
    function clusterItem(i) {
      const ov = document.getElementById('clModal');
      if (!ov || !ov.dataset.zoom) return;
      const [la, ln] = ov.dataset.zoom.split(',').map(Number);
      closeClusterModal();
      try {
        const x = (window.__clItems || [])[i];
        if (!x) return;
        map.flyTo([x.lat, x.lon], Math.max(map.getZoom(), 14), { animate: true });
        map.openPopup(L.popup({ maxWidth: 260 }).setLatLng([x.lat, x.lon]).setContent(buildRichPopup(x)));
      } catch (e) {}
    }


    // Контроль сборки: если прод уже новее — мягкий авто-reload
    (function () {
      if (sessionStorage.getItem('zh-reloaded') === '1') return;
      try {
        fetchTO('/app-version.json?cb=' + Date.now(), { cache: 'no-store' }, 4000).then(function (r) {
          if (!r) return;
          return r.json();
        }).then(function (d) {
          if (d && typeof d.v === 'number' && d.v > ZH_BUILD) {
            sessionStorage.setItem('zh-reloaded', '1');
            try { showToast('Обновляю приложение…'); } catch (e) {}
            setTimeout(function () { location.replace(location.href.split('#')[0]); }, 1200);
          }
        }).catch(function () {});
      } catch (e) {}
    })();
    function openSideMenu() {
      var za = document.querySelector('.zh-ask'); if (za) za.remove();
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
      if (STATIONS_DB && STATIONS_DB.length) {
        let _ref = CITY_LIST.find(x => x.n === name) || null;
        if (!_ref && typeof lat === 'number') {
          let _b = null, _bd = 1e9;
          for (let i = 0; i < CITY_LIST.length; i++) { const _d = haversine([lat, lng], [CITY_LIST[i].lat, CITY_LIST[i].lng]); if (_d < _bd) { _bd = _d; _b = CITY_LIST[i]; } }
          if (_b && _bd < 50) _ref = _b;
        }
        if (!_ref) _ref = { n: name, lat: lat, lng: lng, c: null };
        document.getElementById('cityCountBadge').textContent = cityCountFor(_ref) + ' ЭЗС в базе';
      }
      document.getElementById('weatherCity').textContent = name + ' · Живой прогноз';
      userPos = [lat, lng]; userPosGeo = true;
      map.flyTo(userPos, 12);
      rangeCircle.setLatLng(userPos);
      meMarker.setLatLng(userPos);
      isoLabel.setLatLng(userPos);
      const gtChip = document.getElementById('barGeoText');
      if (gtChip) gtChip.textContent = geoShort(name);
      showToast('Город: ' + name);
      weatherDone = false;
      resetRoute();
      enterIntro();
      loadWeather();
      if (STATIONS_DB) renderNearby();
    }

    function pickCity(city) {
      const c = (typeof city === 'number') ? CITY_LIST[city] : city;
      if (!c || c.lat == null || c.lng == null) { showToast('Город недоступен'); return; }
      activeCity = c.n;
      document.querySelectorAll('.city-pill').forEach(p => p.classList.remove('active'));
      setCityView(c.n, c.lat, c.lng, c.c);
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
        const r = await fetchTO('https://ipwho.is/', { cache: 'no-store' }, 4000);
        const d = await r.json();
        if (d && d.success !== false && d.city && isFinite(d.latitude)) g = { city: d.city, lat: d.latitude, lng: d.longitude };
      } catch (e) {}
      if (!g) {
        try {
          const r = await fetchTO('https://get.geojs.io/v1/ip/geo.json', { cache: 'no-store' }, 4000);
          const d = await r.json();
          if (d && d.city) g = { city: d.city, lat: parseFloat(d.latitude), lng: parseFloat(d.longitude) };
        } catch (e) {}
      }
      if (!g || geoApplied) {
        showToast('Не определили ваш город — выберите его в чипах сверху');
        try { cityStyleInject(); } catch (e) {}
        loadWeather();
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
      try {
        const saved = localStorage.getItem('zh-city');
        if (saved) {
          const hitSaved = CITY_LIST.find(c => c.n === saved);
          if (hitSaved) { pickCity(hitSaved); loadWeather(); return; }
        }
      } catch (e) {}
      cityStyleInject();
      askCity(g);
      loadWeather();
    }

    // === Первый запуск: подтверждение города ===
    function askCity(g) {
      if (document.body.classList.contains('drive')) return;
      const sh = document.createElement('div');
      sh.className = 'zh-ask';
      sh.innerHTML = '<div class="zh-ask-card">'
        + '<div class="zh-ask-q">Вы сейчас в «' + g.city + '»?</div>'
        + '<div class="zh-ask-sub">Откроем карту города, ближайшие ЭЗС и живую погоду</div>'
        + '<div class="zh-ask-btns"><button class="zh-ask-yes" id="askYes">Да, показать</button><button class="zh-ask-no" id="askNo">Выбрать другой</button></div>'
        + '</div>';
      document.body.appendChild(sh);
      try { sh.querySelector('#askYes').onclick = () => {
        try { localStorage.setItem('zh-city', g.city); } catch (e) {}
        sh.remove();
        const hit = CITY_LIST.find(c => c.n === g.city);
        if (hit) pickCity(hit);
        else { activeCity = g.city; setCityView(g.city, g.lat, g.lng); }
        loadWeather();
      }; sh.querySelector('#askNo').onclick = () => { sh.remove(); openCitySheet(); loadWeather(); }; } catch (e) {}
    }
    function cityStyleInject() {
      if (document.getElementById('zh-ask-style')) return;
      const s = document.createElement('style'); s.id = 'zh-ask-style';
      s.textContent = '.zh-ask{position:fixed;inset:0;z-index:900;background:rgba(0,0,0,.55);display:flex;align-items:flex-end;justify-content:center;padding:0 10px calc(96px + env(safe-area-inset-bottom))}'
        + '.zh-ask-card{background:#111114;border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:18px 16px;max-width:340px;width:100%;box-shadow:0 -12px 60px rgba(0,0,0,.6)}'
        + '.zh-ask-q{font-size:16px;font-weight:700;color:#fff;letter-spacing:-.02em}'
        + '.zh-ask-sub{font-size:12px;color:rgba(255,255,255,.6);margin-top:6px}'
        + '.zh-ask-btns{display:flex;gap:8px;margin-top:14px}'
        + '.zh-ask-yes{flex:1.4;background:#E85002;color:#fff;border:none;border-radius:12px;padding:13px 10px;font-size:13px;font-weight:700;cursor:pointer}'
        + '.zh-ask-no{flex:1;background:rgba(255,255,255,.06);color:rgba(255,255,255,.85);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:13px 8px;font-size:12px;cursor:pointer}'
        + '@media(min-width:821px){.zh-ask{align-items:center}}';
      document.head.appendChild(s);
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
      if (mins < 60) return '~' + mins + ' м';
      return '~' + Math.floor(mins / 60) + ' ч ' + (mins % 60 ? (mins % 60) + ' м' : '');
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
        updateChipCounts();
        try { refreshCityCounts(); } catch (e) {}
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
        try { refreshCityCounts(); } catch (e) {}
      }).catch(() => {});
    }

    let stCluster = null; let mapFilterCat = null;
    let baseMode = 'all';
    let OSM_FULL = null;
    let osmLoading = false;

    function renderAllStations() {
      if (!STATIONS_DB || !STATIONS_DB.length || typeof L.markerClusterGroup !== 'function') return;
      if (stCluster) { stCluster.clearLayers(); }
      else {
        stCluster = L.markerClusterGroup({ chunkedLoading: true, animate: false, showCoverageOnHover: true, maxClusterRadius: 64, disableClusteringAtZoom: 14, zoomToBoundsOnClick: false,
          polygonOptions: { color: '#00E5FF', weight: 1.2, fillColor: '#00E5FF', fillOpacity: 0.06, dashArray: '4,6', interactive: false } });
        map.addLayer(stCluster);
      }
      const pts = [];
      const srcList = (baseMode === 'osm') ? (OSM_FULL || []) : STATIONS_DB.concat(((baseMode === 'all' && OSM_FULL) ? OSM_FULL : []));
      srcList.forEach((x) => {
        if (typeof x.lat !== 'number' || typeof x.lon !== 'number') return;
        if (baseMode === 'base' && (x.src === 'yandex' || x.src === 'osm')) return;
        if (baseMode === 'yandex' && x.src !== 'yandex') return;
        if (baseMode === 'osm' && x.src !== 'osm') return;
        if (mapFilterCat) { if (catOf(x) !== mapFilterCat) return; }
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
        st.zhData = x;
        st.bindPopup(function () { return buildRichPopup(x); }, { maxWidth: 260 });
        pts.push(st);
      });
      stCluster.addLayers(pts);
      const sw = document.getElementById('baseSwitch');
      if (sw) {
        const nb = STATIONS_DB.filter(x => x.src === 'yandex').length;
        const no = STATIONS_DB.filter(x => x.src === 'osm').length;
        const q = (sel, txt) => { const el = sw.querySelector(sel); if (el) el.textContent = txt; };
        const _obc = document.getElementById('ourBaseCount');
      if (_obc) _obc.textContent = STATIONS_DB.length.toLocaleString('ru-RU');
      q('[data-mode=all]', 'Всё · ' + (STATIONS_DB.length + (OSM_FULL ? OSM_FULL.length : 0)).toLocaleString('ru-RU'));
        q('[data-mode=base]', 'Наши · ' + (STATIONS_DB.length - nb - no).toLocaleString('ru-RU'));
        q('[data-mode=yandex]', 'Яндекс · ' + nb.toLocaleString('ru-RU'));
        q('[data-mode=osm]', 'OSM · ' + ((OSM_FULL && OSM_FULL.length) || no).toLocaleString('ru-RU'));
      }
      showToast('Все ' + pts.length.toLocaleString('ru-RU') + ' станций на карте');
    }


    function buildRichPopup(x) {
      const conn = (x.s || []).join(', ');
      const pw = Number(x.pw) || 0;
      const lowConn = conn.toLowerCase();
      const srcNote = x.src === 'yandex' ? '<div class="st-pop-src" style="margin-top:5px;font-size:11px;color:#8a8f98">Источник: Яндекс.Карты — мощность и порты могут отсутствовать</div>'
        : (x.src === 'ocm' ? '<div class="st-pop-src" style="margin-top:5px;font-size:11px;color:#8a8f98">Источник: Open Charge Map' + (x.u ? ' — по этой станции мало данных</div><div class="st-pop-src" style="margin-top:3px;font-size:11px;color:#f59e0b;font-weight:600">⚠ Нет информации: мощность и разъёмы не подтверждены' : '</div>')
        : (x.src === 'osm' || x.src === 'osm2' ? '<div class="st-pop-src" style="margin-top:5px;font-size:11px;color:#8a8f98">Источник: OpenStreetMap (ODbL) — мощность и порты могут отсутствовать</div>' : ''));
      const carTitle = (document.getElementById('carModelTitle') || {}).textContent || '';
      const portLine = (document.getElementById('carPortTag') || {}).textContent || '';
      const mdl = (typeof MODELS_ALL !== 'undefined' && MODELS_ALL) ? MODELS_ALL.find(m => m.name === carTitle) : null;
      const carPort = (portLine.split('·')[0] || '').trim().toLowerCase();
      let fitLine = '';
      if (carPort) {
        if (conn && lowConn.replace(/\s/g, '').indexOf(carPort.replace(/\s/g, '')) >= 0) {
          fitLine = '<div style="margin-top:7px;font-size:12px;color:#16a34a;font-weight:600">Прямое подключение для вашей модели</div>';
        } else if (carPort.indexOf('gb/t') >= 0 && /ccs|type2/.test(lowConn.replace(/\s/g, ''))) {
          fitLine = '<div style="margin-top:7px;font-size:12px;color:#f59e0b;font-weight:600">Через адаптер — подходит для вашей модели</div>'
            + '<div style="margin-top:3px"><a href="/razemy/" style="color:#FF8F33;font-size:12px;text-decoration:underline">Адаптер в каталоге →</a></div>';
        }
      }
      let cabLine = '';
      if (/type\s*2/i.test(conn) && !/ccs|gb\/t|gb_dc|type2_combo/i.test(conn) && !/кабел|socket/i.test(conn)) {
        cabLine = '<div style="margin-top:6px;font-size:11px;color:#8a8f98">Тип Type 2 не уточнён — возьмите свой кабель на случай, если на станции только розетка <a href="/razemy/" style="color:#FF8F33">Кабели и адаптеры →</a></div>';
      }
      let sessLine = '';
      if (mdl && mdl.cap && pw) {
        const mins = Math.max(10, Math.round((0.6 * mdl.cap) / (pw * 0.8) * 60));
        sessLine = '<div style="margin-top:6px;font-size:12px;color:#D9C3AB">Сессия 20 → 80%: ~' + mins + ' мин</div>';
      }
      const tgText = encodeURIComponent('Статус станции: ' + (x.op || x.n || '') + (x.a ? ' — ' + x.a : '') + '. Разъёмы: ' + (conn || '—') + (pw ? ', ' + pw + ' кВт' : '') + '. Отметка: ');
      const routeHref = 'https://yandex.ru/maps/?rtext=' + encodeURIComponent((userPosGeo ? '~' : userPos[0] + ',' + userPos[1] + '~') + x.lat + ',' + x.lon) + '&rtt=auto';
      const srcBadge = x.src === 'yandex' ? ' · Я' : (x.src === 'osm' || x.src === 'osm2' ? ' · OSM' : '');
      return '<div class="st-pop">'
        + '<div class="st-pop-name">' + (x.op || x.n || 'ЭЗС') + srcBadge + '</div>'
        + '<div class="st-pop-addr">' + (x.a && x.a !== 'Адрес не указан' ? x.a : '') + '</div>'
        + srcNote
        + '<div class="st-pop-grid"><div><span>Мощность</span><b>' + kwLabel(pw) + '</b></div><div><span>Порты</span><b>' + (x.s && x.s.length ? x.s.join(', ') : '—') + '</b></div></div>'
        + cabLine + fitLine + sessLine
        + '<button class="st-pop-btn" onclick="buildRoute(' + x.lat + ',' + x.lon + ')" style="margin-top:10px;width:100%">Маршрут от меня · хватит ли</button>'
        + '<a class="st-pop-btn" href="' + routeHref + '" target="_blank" rel="noopener" style="margin-top:6px">Маршрут в Яндекс.Карты</a>'
        + '<div style="margin-top:8px;display:flex;flex-direction:column;gap:3px">'
        + '<a href="https://yandex.ru/maps/?pt=' + x.lon + ',' + x.lat + '&z=17&l=map" target="_blank" rel="noopener" style="color:#FF8F33;font-size:12px">Открыть в Яндекс.Картах →</a>'
        + '<a href="https://2chargers.ru/" target="_blank" rel="noopener" style="color:#FF8F33;font-size:12px">Статус в 2Chargers →</a>'
        + '<a href="https://t.me/zapashoda_ev_bot?text=' + tgText + '" target="_blank" rel="noopener" style="color:#FF8F33;font-size:12px">Сообщить статус станции →</a>'
        + '</div></div>';
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
      let near = STATIONS_DB
        .map(x => ({ x: x, d: haversine(userPos, [x.lat, x.lon]) }))
        .filter(v => v.d <= 30)
        .sort((a, b) => a.d - b.d)
        .slice(0, 10);
      if (!near.length) {
        near = STATIONS_DB
          .map(x => ({ x: x, d: haversine(userPos, [x.lat, x.lon]) }))
          .filter(v => v.d <= 150)
          .sort((a, b) => a.d - b.d)
          .slice(0, 10);
      }
      if (!near.length) return;
      try {
        const maxKm = (typeof near[0].d === 'number') ? (Math.round(near[0].d * 10) / 10) : 0;
        const ttl = document.querySelector('.st-table-title');
        if (ttl) ttl.textContent = 'Рядом с вами · ' + near.length + ' ' + pluralSt(near.length) + ' до ' + (Math.round(maxKm * 10) / 10) + ' км';
      } catch (e) {}
      near = near.map(v => ({
          name: (v.x.op || v.x.n || 'ЭЗС'),
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
      showToast(state.roundTrip ? 'Возврат учтён: туда и обратно' : 'Возврат отключён: только до станции');
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
      const N = (t) => { const n = countTypeInCity(t); return n + ' ' + pluralSt(n); };
      const M = {
        route: 'Открываем маршрут в Яндекс.Картах',
        memo: 'Памятка сохранена',
        link: 'Ссылка на ЭЗС скопирована',
        'filter-gbt': () => 'Фильтр: GB/T DC — ' + N('gb/t') + ' в ' + cityIn(),
        'filter-ccs': () => 'Фильтр: CCS2 через переходник — ' + N('ccs') + ' в ' + cityIn(),
        'filter-ac': () => 'Фильтр: Type 2 AC — ' + N('type 2') + ' в ' + cityIn(),
        'filter-chademo': () => 'Фильтр: CHAdeMO — ' + N('chademo') + ' в ' + cityIn()
      };
      showToast(typeof M[key] === 'function' ? M[key]() : M[key]);
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
    let _ccCache = null;
    const R_BY_CITY = {'Москва': 35, 'Санкт-Петербург': 25, 'Красноярск': 15, 'Казань': 15, 'Нижний Новгород': 15, 'Челябинск': 15, 'Самара': 15, 'Тюмень': 15, 'Волгоград': 15, 'Тула': 15, 'Липецк': 15, 'Новосибирск': 15, 'Набережные Челны': 15, 'Ростов-на-Дону': 15, 'Кемерово': 15, 'Ярославль': 15, 'Иркутск': 15, 'Екатеринбург': 15, 'Пермь': 15, 'Хабаровск': 15, 'Краснодар': 15, 'Томск': 15, 'Сочи': 15, 'Ульяновск': 15, 'Оренбург': 15, 'Иваново': 15, 'Чебоксары': 15, 'Калининград': 15, 'Химки': 6, 'Реутов': 6, 'Нижнекамск': 8, 'Севастополь': 12, 'Калуга': 10, 'Йошкар-Ола': 10, 'Владимир': 10};
    function cityCountFor(c) {
      if (!STATIONS_DB || !STATIONS_DB.length) return (c.c != null ? c.c : null);
      if (!_ccCache) _ccCache = {};
      if (_ccCache[c.n] == null) {
        let n = 0;
        for (let i = 0; i < STATIONS_DB.length; i++) {
          const s = STATIONS_DB[i];
          if (typeof s.lat !== 'number' || typeof s.lon !== 'number') continue;
          if (Math.abs(s.lat - c.lat) > 0.6 || Math.abs(s.lon - c.lng) > 0.9) continue;
          if (haversine([c.lat, c.lng], [s.lat, s.lon]) <= (R_BY_CITY[c.n] || 10)) n++;
        }
        _ccCache[c.n] = n;
      }
      return _ccCache[c.n];
    }
    function pluralSt(n) { n = Number(n) || 0; return (n % 10 === 1 && n % 100 !== 11) ? 'станция' : ([2,3,4].indexOf(n % 10) >= 0 && [12,13,14].indexOf(n % 100) < 0) ? 'станции' : 'станций'; }
    function activeCityRef() {
      let c = CITY_LIST.find(x => x.n === activeCity);
      if (!c && userPos) {
        let best = null, bd = 1e9;
        for (let i = 0; i < CITY_LIST.length; i++) { const d = haversine(userPos, [CITY_LIST[i].lat, CITY_LIST[i].lng]); if (d < bd) { bd = d; best = CITY_LIST[i]; } }
        if (best && bd < 50) c = best;
      }
      return c || (userPos ? { n: activeCity, lat: userPos[0], lng: userPos[1] } : null);
    }
    function countTypeInCity(t) {
      const c = activeCityRef(); if (!c || !STATIONS_DB || !STATIONS_DB.length) return 0;
      let n = 0;
      for (let i = 0; i < STATIONS_DB.length; i++) {
        const s = STATIONS_DB[i];
        if (typeof s.lat !== 'number' || typeof s.lon !== 'number') continue;
        if (Math.abs(s.lat - c.lat) > 0.6 || Math.abs(s.lon - c.lng) > 0.9) continue;
        if (haversine([c.lat, c.lng], [s.lat, s.lon]) > (R_BY_CITY[c.n] || 10)) continue;
        if ((s.s || []).some(x => (x || '').toLowerCase().indexOf(t) >= 0)) n++;
      }
      return n;
    }
    const _CHIP_ALIAS = { 'СПб': 'Санкт-Петербург', 'Н. Новгород': 'Нижний Новгород' };
    function cityIn() {
      const n = displayCity(); if (!n) return 'городе';
      const map = { 'Нижний Новгород':'Нижнем Новгороде', 'Санкт-Петербург':'Санкт-Петербурге', 'Ростов-на-Дону':'Ростове-на-Дону', 'Великий Новгород':'Великом Новгороде' };
      if (map[n]) return map[n];
      const parts = n.split(' ');
      let last = parts[parts.length - 1];
      if (/(ово|ево|ино|ыно)$/i.test(last)) return n;
      if (last.endsWith('ь')) last = last.slice(0, -1) + 'и';
      else if (last.endsWith('а')) last = last.slice(0, -1) + 'е';
      else if (last.endsWith('я')) last = last.slice(0, -1) + 'и';
      else last = last + 'е';
      parts[parts.length - 1] = last;
      return parts.join(' ');
    }
    function refreshCityCounts() {
      _ccCache = null;
      const c = activeCityRef();
      if (c) { const el = document.getElementById('cityCountBadge'); if (el) el.textContent = cityCountFor(c) + ' ЭЗС в базе'; }
      document.querySelectorAll('#cityChips .city-pill').forEach(p => {
        const t = p.textContent.split('·');
        if (t.length < 2) return;
        const nm = _CHIP_ALIAS[t[0].trim()] || t[0].trim();
        const hit = CITY_LIST.find(x => x.n === nm);
        if (hit) p.textContent = t[0].trim() + ' · ' + cityCountFor(hit);
      });
      renderCityGrid();
    }


    // pickCity и pickCityChip объявлены ниже (единая setCityView)

    function renderCityGrid() {
      document.getElementById('cityGrid').innerHTML = CITY_LIST.map(c => `
        <div class="city-cell ${c.n === activeCity ? 'active' : ''}" onclick="pickCity(${CITY_LIST.indexOf(c)})">
          ${c.n} <b>${cityCountFor(c)}</b>
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
      try { localStorage.setItem('zh-car', JSON.stringify({ name: name, base: base, port: port, direct: direct, est: est })); } catch (e) {}
      if (base == null) {
        document.getElementById('carModelTitle').textContent = name;
        document.getElementById('carPortTag').textContent = port || '—';
        document.getElementById('carBaseKm').textContent = 'Паспортный запас не указан — расчёт по последней модели: ' + state.baseKm + ' км';
        document.getElementById('compatText').textContent = direct ? 'Напрямую DC' : 'Через адаптер';
        closeCarModal();
        showToast('Модель выбрана: ' + name);
        return;
      }
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
      const url = 'https://yandex.ru/maps/?rtext=' + encodeURIComponent((userPosGeo ? '~' : userPos[0] + ',' + userPos[1] + '~') + st.coords[0] + ',' + st.coords[1]) + '&rtt=auto';
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
              <div class="st-addr">${s.addr}&nbsp;·&nbsp;${s.km} км</div>
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
    try { const _bs = document.getElementById('baseSwitch'); if (_bs) _bs.remove(); } catch (e) {}
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

    // === Волна 18.11 #2: погода в виджете 3, зимний блок виджета 5, память заряда, мобильные фиксы ===
    function nearestTempIdx(t) {
      let idx = 4, best = 1e9;
      CHART_TEMPS.forEach((ct, i) => {
        const num = parseFloat(String(ct).replace('+', '').replace('°', ''));
        if (!isFinite(num)) return;
        const d = Math.abs(num - t);
        if (d < best) { best = d; idx = i; }
      });
      return idx;
    }
    function updateWinterBox() {
      const box = document.getElementById('winterBox');
      if (!box) return;
      let soc = parseInt(document.getElementById('socSlider').value, 10) || 80;
      const t = (typeof state.temp === 'number') ? state.temp : null;
      const pct = t === null ? 72 : CHART_PCTS[nearestTempIdx(t)];
      const full = Math.round(state.baseKm * pct / 100);
      const cur = Math.round(full * soc / 100);
      const lbl = t === null ? '−15°' : ((t > 0 ? '+' + t : String(t)) + '°');
      const slug = window.__zhModelSlug || null;
      if (!box.firstChild) {
        const modelLine = slug
          ? '<a id="wbLink" href="/models/' + slug + '/" style="color:var(--orange);font-size:11.5px;text-decoration:none">Зимние болячки и решения по вашей модели →</a>'
          : '<a id="wbLink" href="/models/" style="color:var(--orange);font-size:11.5px;text-decoration:none">154 модели: зимние болячки и решения →</a>';
        box.innerHTML =
          '<div class="wb-now" id="wbNow"></div>' +
          '<ul class="wb-tips">' +
          '<li>Салон прогрейте, пока машина на зарядке — сохраните до 10–15% пробега</li>' +
          '<li>Климат 18–20° вместо максимума: минус 5–8% к расходу</li>' +
          '<li>На трассе 90–100 км/ч вместо 110: плюс 10–15% к пробегу</li>' +
          '</ul>' + modelLine;
      }
      const now = document.getElementById('wbNow');
      if (now) now.innerHTML = 'При ' + lbl + ': полный заряд ≈ ' + full + ' км · на вашем заряде (' + soc + '%) ≈ <b style="color:var(--text-white)">' + cur + ' км</b>';
      const link = document.getElementById('wbLink');
      if (link && slug) link.setAttribute('href', '/models/' + slug + '/');
    }
    (function zhInitWave2() {
      // Виджет 4: имя про заряд
      document.querySelectorAll('.card-label span').forEach(function(sp) {
        const tx = (sp.textContent || '').trim();
        if (tx.indexOf('4. Сколько проеду сейчас') === 0) sp.textContent = '4. Реальный запас хода';
      });
      // Подсказка под формулой
      const hf = document.getElementById('heroFormula');
      if (hf && !document.getElementById('socHint')) {
        const d = document.createElement('div');
        d.id = 'socHint';
        d.style.cssText = 'font-size:11px;color:var(--text-dim);margin-top:6px';
        d.textContent = 'Поставьте фактический уровень заряда — пересчитаем с учётом погоды за окном';
        hf.insertAdjacentElement('afterend', d);
      }
      // Память уровня заряда между сессиями PWA (обёртка над setSoc — программные установки тоже пишем)
      if (!window.__zhSocPatched && typeof window.setSoc === 'function') {
        window.__zhSocPatched = true;
        const _prevSetSoc = window.setSoc;
        window.setSoc = function(v) { _prevSetSoc(v); try { localStorage.setItem('zh-soc-dash', v); } catch (e) {} };
      }
      try { const sv = parseInt(localStorage.getItem('zh-soc-dash') || '', 10); if (sv >= 10 && sv <= 100) window.setSoc(sv); } catch (e) {}
      const sl = document.getElementById('socSlider');
      if (sl) sl.addEventListener('input', function() { try { localStorage.setItem('zh-soc-dash', sl.value); } catch (e) {} });
      // Мобильные фиксы: пустая оранжевая кнопка в шапке + дубль «К карте» под крестиком списка
      const st = document.createElement('style');
      st.id = 'zh-mob-fix';
      st.textContent = '@media(max-width:820px){.glass-pill .btn-primary{display:none!important}.st-table-head .btn-ghost{display:none!important}}';
      document.head.appendChild(st);
      // Зимний блок в карточке 5
      const pl = document.getElementById('passportLabel');
      if (pl) {
        const card = pl.closest('.card');
        if (card && !document.getElementById('winterBox')) {
          const d = document.createElement('div');
          d.id = 'winterBox';
          d.className = 'winter-box';
          card.appendChild(d);
        }
      }
      const css = document.createElement('style');
      css.id = 'zh-winter-css';
      css.textContent = '.winter-box{margin-top:10px;border-top:1px solid rgba(255,255,255,.08);padding-top:10px;font-size:11.5px;color:var(--text-dim);display:flex;flex-direction:column;gap:6px}.wb-now{color:var(--text-white);font-weight:600;font-size:12.5px;line-height:1.35}.wb-tips{margin:0;padding-left:16px;display:flex;flex-direction:column;gap:3px}.wb-tips li::marker{color:var(--orange)}';
      document.head.appendChild(css);
      updateWinterBox();
    })();

    // === Волна 18.11 #3: маршрут на карте с расчётом запаса ===
    let routeLine = null, routeEnd = null;
    window.__routeSt = [];
    function resetRoute() {
      if (routeLine) { map.removeLayer(routeLine); routeLine = null; }
      if (routeEnd) { map.removeLayer(routeEnd); routeEnd = null; }
      const p = document.getElementById('routePanel');
      if (p) p.classList.remove('show');
    }
    function makeStartHere() {
      if (routeEnd && routeEnd._latlng) {
        userPos = [routeEnd._latlng.lat, routeEnd._latlng.lng];
        userPosGeo = false;
        rangeCircle.setLatLng(userPos);
        if (typeof meMarker !== 'undefined') meMarker.setLatLng(userPos);
        if (typeof isoLabel !== 'undefined') isoLabel.setLatLng(userPos);
        recalc(false);
      }
      resetRoute();
    }
    function displayCity() {
      if (CITY_LIST && CITY_LIST.some(c => c.n === state.city)) return state.city;
      if (userPos && CITY_LIST && CITY_LIST.length) {
        let best = null, bd = 1e18;
        CITY_LIST.forEach(c => {
          if (typeof c.lat !== 'number') return;
          const dx = (c.lat - userPos[0]) * 111, dy = (c.lng - userPos[1]) * 111 * Math.cos(userPos[0] * Math.PI / 180);
          const d = dx * dx + dy * dy;
          if (d < bd) { bd = d; best = c; }
        });
        if (best) return best.n;
      }
      return state.city || 'Ваш город';
    }
    function distToSegM(p, a, b) {
      const kx = Math.cos(p[0] * Math.PI / 180);
      const ax = a[0], ay = a[1] * kx, bx = b[0], by = b[1] * kx, px = p[0], py = p[1] * kx;
      const dx = bx - ax, dy = by - ay;
      const L2 = dx * dx + dy * dy;
      let t = L2 ? ((px - ax) * dx + (py - ay) * dy) / L2 : 0;
      t = Math.max(0, Math.min(1, t));
      const qx = ax + t * dx, qy = ay + t * dy;
      return Math.hypot((px - qx) * 111000, (py - qy) * 111000);
    }
    function stationsAlongRoute(geom, maxDevM) {
      let minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
      geom.forEach(c => { minLat = Math.min(minLat, c[0]); maxLat = Math.max(maxLat, c[0]); minLon = Math.min(minLon, c[1]); maxLon = Math.max(maxLon, c[1]); });
      const cand = (STATIONS_DB || []).filter(x => typeof x.lat === 'number' && typeof x.lon === 'number' &&
        x.lat > minLat - 0.05 && x.lat < maxLat + 0.05 && x.lon > minLon - 0.05 && x.lon < maxLon + 0.05);
      const out = [];
      cand.forEach(x => {
        const p = [x.lat, x.lon];
        let best = 1e12, prog = 0;
        for (let i = 1; i < geom.length; i++) {
          const d = distToSegM(p, geom[i - 1], geom[i]);
          if (d < best) { best = d; prog = i / geom.length; }
        }
        if (best <= maxDevM) out.push({ x: x, prog: prog });
      });
      out.sort((a, b) => a.prog - b.prog);
      return out.slice(0, 3).map(o => o.x);
    }
    function focusRouteStation(i) {
      const x = (window.__routeSt || [])[i];
      if (!x) return;
      try { L.popup().setLatLng([x.lat, x.lon]).setContent(function () { return buildRichPopup(x); }).openOn(map); map.flyTo([x.lat, x.lon], 14); } catch (e) {}
    }
    function showRoutePanel(ok, distKm, rest, durTxt, src, along) {
      const p = document.getElementById('routePanel');
      if (!p) return;
      const dm = String(distKm).replace('.', ',');
      let html = '<div class="rp-line">Маршрут: ' + dm + ' км' + durTxt + ' <span style="color:var(--text-dim);font-weight:500">(' + src + ')</span></div>';
      html += ok
        ? '<div class="rp-sub" style="color:#00E5FF">Хватит с запасом: останется ≈ ' + rest + ' км</div>'
        : '<div class="rp-sub" style="color:#FF6F6F">Не хватит ≈ ' + Math.abs(rest) + ' км — зарядки по пути:</div>';
      if (along && along.length) {
        window.__routeSt = along;
        html += '<div class="rp-st">' + along.map((x, i) => {
          const nm = x.op || x.n || 'ЭЗС';
          const pw = x.pw ? (Number(x.pw) ? Number(x.pw) + ' кВт' : '') : '';
          return '<div class="rp-st-item" onclick="focusRouteStation(' + i + ')"><b>' + (i + 1) + '. ' + escN(nm) + '</b><small>' + (x.a || '') + (pw ? ' · ' + pw : '') + '</small></div>';
        }).join('') + '</div>';
      } else window.__routeSt = [];
      html += '<div class="rp-btns"><button onclick="resetRoute()">Сбросить</button><button onclick="makeStartHere()">Сделать точкой старта</button></div>';
      p.innerHTML = html;
      p.style.borderLeftColor = ok ? '#00E5FF' : '#FF3B30';
      p.classList.add('show');
    }
    async function buildRoute(dlat, dlon) {
      try {
        if (!userPos) return;
        resetRoute();
        routeEnd = L.circleMarker([dlat, dlon], { radius: 6, color: '#fff', weight: 2, fillColor: '#00E5FF', fillOpacity: 1 }).addTo(map);
        let dist = null, dur = null, geom = null, src = 'по дорогам';
        try {
          const r = await fetchTO('https://router.project-osrm.org/route/v1/driving/' + userPos[1].toFixed(5) + ',' + userPos[0].toFixed(5) + ';' + dlon.toFixed(5) + ',' + dlat.toFixed(5) + '?overview=full&geometries=geojson', { cache: 'no-store' }, 7000);
          if (r && r.ok) {
            const d = await r.json();
            if (d && d.code === 'Ok' && d.routes && d.routes[0]) {
              dist = d.routes[0].distance; dur = d.routes[0].duration;
              geom = (d.routes[0].geometry.coordinates || []).map(c => [c[1], c[0]]);
            }
          }
        } catch (e) {}
        if (dist === null || dist < 150) { dist = haversine(userPos, [dlat, dlon]) * 1.25; src = 'по прямой ×1,25'; }
        const distKm = Math.round(dist / 100) / 10;
        const soc = parseInt(document.getElementById('socSlider').value, 10) || 80;
        const km = Math.round(state.baseKm * (soc / 100) * state.mult);
        const rest = Math.round(km - distKm);
        const ok = rest >= 0;
        const durTxt = dur ? ' · ~' + Math.round(dur / 60) + ' мин' : '';
        const co = ok ? '#00E5FF' : '#FF3B30';
        if (geom && geom.length > 1) {
          routeLine = L.polyline(geom, { color: co, weight: 4, opacity: 0.9 }).addTo(map);
        } else {
          routeLine = L.polyline([userPos, [dlat, dlon]], { color: co, weight: 4, dashArray: '6,8', opacity: 0.85 }).addTo(map);
        }
        try { map.fitBounds(routeLine.getBounds(), { padding: [40, 40] }); } catch (e) {}
        let along = [];
        if (!ok) along = stationsAlongRoute(geom || [userPos, [dlat, dlon]], 4000);
        showRoutePanel(ok, distKm, rest, durTxt, src, along);
      } catch (err) { showToast('Маршрут не построился — тапните ещё раз'); }
    }
    (function zhInitRoute() {
      if (!document.getElementById('routePanel')) {
        const p = document.createElement('div');
        p.id = 'routePanel';
        document.body.appendChild(p);
      }
      const css = document.createElement('style');
      css.id = 'zh-route-css';
      css.textContent = '.st-pop button.st-pop-btn{border:0;background:rgba(232,80,2,.16);color:#FF8F33;font:inherit}#routePanel{position:fixed;left:50%;transform:translateX(-50%);width:min(92vw,460px);bottom:calc(64px + env(safe-area-inset-bottom));z-index:70;background:rgba(11,11,13,.97);border:1px solid rgba(255,255,255,.09);border-left:3px solid #00E5FF;border-radius:14px;padding:12px 14px;display:none;font-variant-numeric:tabular-nums;box-shadow:0 16px 40px rgba(0,0,0,.65)}#routePanel.show{display:block}.rp-line{color:var(--text-white);font-weight:600;font-size:13.5px}.rp-sub{color:var(--text-dim);font-size:12px;margin-top:3px}.rp-st{margin-top:8px;display:flex;flex-direction:column;gap:4px}.rp-st-item{font-size:12px;color:var(--text-white);background:rgba(255,255,255,.05);border-radius:8px;padding:11px 10px;cursor:pointer}.rp-st-item small{color:var(--text-dim);display:block;margin-top:1px}.rp-btns{margin-top:10px;display:flex;gap:8px}.rp-btns button{flex:1;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:var(--text-white);border-radius:10px;padding:13px 8px;font-size:12px;cursor:pointer}';
      document.head.appendChild(css);
    })();
  