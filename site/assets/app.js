(function () {
  'use strict';

  // Die drei Vantic-Ebenen. Farben aufgehellt, damit sie auf dunklen Karten sichtbar sind.
  var EBENEN = {
    strategie: { farbe: '#9AA1A8', name: 'Strategie und Technologie' },
    organisation: { farbe: '#6FA58C', name: 'Organisation und Prozesse' },
    mensch: { farbe: '#E2B04A', name: 'Mensch und Kultur' }
  };
  var PALETTE = ['#E2B04A', '#6FA58C', '#9AA1A8'];
  var state = { data: null, filter: 'alle', selected: null, install: false };

  var chipsEl = document.getElementById('chips');
  var listEl = document.getElementById('skill-list');
  var detailEl = document.getElementById('skill-detail');

  // Kleine Hilfsfunktion zum sicheren Erzeugen von Elementen (kein innerHTML mit Daten)
  function h(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value == null) return;
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key.slice(0, 2) === 'on') node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value);
    });
    (children || []).forEach(function (child) {
      if (child == null) return;
      node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    });
    return node;
  }

  function color(category, ebene) {
    if (ebene && EBENEN[ebene]) return EBENEN[ebene].farbe;
    var index = state.data.kategorien.indexOf(category);
    return PALETTE[(index < 0 ? 0 : index) % PALETTE.length];
  }

  function dot(category, ebene) {
    var d = h('span', { class: 'dot', 'aria-hidden': 'true' });
    d.style.background = color(category, ebene);
    return d;
  }

  function chevron() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'chevron');
    svg.setAttribute('width', '22');
    svg.setAttribute('height', '22');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', '#BFD0C5');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M9 6l6 6-6 6');
    svg.appendChild(path);
    return svg;
  }

  function downloadIcon() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '18');
    svg.setAttribute('height', '18');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    ['M12 4v11', 'M7 11l5 5 5-5', 'M5 20h14'].forEach(function (d) {
      var p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', d);
      svg.appendChild(p);
    });
    return svg;
  }

  function copyBlock(text) {
    var btn = h('button', { type: 'button', class: 'copy', text: 'Kopieren' });
    btn.addEventListener('click', function () {
      if (!navigator.clipboard || !navigator.clipboard.writeText) return;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Kopiert';
        setTimeout(function () { btn.textContent = 'Kopieren'; }, 1800);
      }, function () {});
    });
    return h('div', { class: 'code' }, [h('code', { text: text }), btn]);
  }

  function visibleSkills() {
    return state.data.skills.filter(function (s) {
      return state.filter === 'alle' || s.kategorie === state.filter;
    });
  }

  function renderChips() {
    chipsEl.textContent = '';
    var categories = state.data.kategorien;
    if (categories.length < 2) {
      chipsEl.hidden = true;
      return;
    }
    chipsEl.hidden = false;
    ['alle'].concat(categories).forEach(function (cat) {
      chipsEl.appendChild(h('button', {
        type: 'button',
        class: 'chip',
        'data-filter': cat,
        'aria-pressed': String(state.filter === cat),
        text: cat === 'alle' ? 'Alle' : cat,
        onclick: function () {
          state.filter = cat;
          state.install = false;
          var first = visibleSkills()[0];
          state.selected = first ? first.id : null;
          render('chip:' + cat);
        }
      }));
    });
  }

  function renderList(skills) {
    listEl.textContent = '';
    if (!skills.length) {
      listEl.appendChild(h('p', { class: 'notice', text: 'Noch keine Skills veröffentlicht.' }));
      return;
    }
    skills.forEach(function (s) {
      listEl.appendChild(h('button', {
        type: 'button',
        class: 'skill-card',
        'data-id': s.id,
        'aria-pressed': String(s.id === state.selected),
        onclick: function () {
          state.selected = s.id;
          state.install = false;
          render('card:' + s.id);
          if (window.matchMedia('(max-width: 960px)').matches) {
            detailEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      }, [
        h('span', { class: 'card-body' }, [
          h('span', { class: 'cat' }, [dot(s.kategorie, s.ebene), h('span', { text: s.kategorie })]),
          h('span', { class: 'card-title', text: s.titel }),
          h('span', { class: 'card-text', text: s.kurzbeschreibung })
        ]),
        chevron()
      ]));
    });
  }

  function renderInstall(s) {
    var cfg = state.data.config;
    return h('div', { class: 'install' }, [
      h('div', { class: 'block' }, [
        h('h4', { text: 'In Claude installieren (Web und Desktop)' }),
        h('div', { class: 'steps' }, [
          h('div', { text: '1. Lade die Zip-Datei des Skills herunter.' }),
          h('div', { text: '2. Öffne in Claude die Einstellungen, dann Capabilities und Skills. Code-Ausführung und Dateierstellung müssen aktiviert sein.' }),
          h('div', { text: '3. Lade die Zip-Datei über «Skill hochladen» hoch und schalte den Skill ein.' })
        ])
      ]),
      h('div', { class: 'block' }, [
        h('h4', { text: 'In Claude Code installieren, alle Vantic Skills' }),
        copyBlock('/plugin marketplace add ' + cfg.github),
        copyBlock('/plugin install ' + cfg.plugin + '@' + cfg.marketplace)
      ]),
      h('div', { class: 'block' }, [
        h('h4', { text: 'In Claude Code installieren, nur dieser Skill' }),
        h('p', { class: 'hint', text: 'Entpacke die Zip-Datei in den Ordner ~/.claude/skills/. Danach liegt der Skill unter ~/.claude/skills/' + s.id + '/.' })
      ])
    ]);
  }

  function renderDetail(s) {
    detailEl.textContent = '';
    if (!s) {
      detailEl.hidden = true;
      return;
    }
    detailEl.hidden = false;

    detailEl.appendChild(h('div', { class: 'block' }, [
      h('div', { class: 'cat' }, [dot(s.kategorie, s.ebene), h('span', { text: s.kategorie + (EBENEN[s.ebene] ? ', Ebene ' + EBENEN[s.ebene].name : '') })]),
      h('h3', { text: s.titel }),
      h('p', { class: 'lead', text: s.einleitung })
    ]));

    if (s.punkte && s.punkte.length) {
      detailEl.appendChild(h('div', { class: 'block' },
        [h('h4', { text: 'Das macht der Skill' })].concat(
          s.punkte.map(function (t) { return h('div', { class: 'point', text: t }); })
        )));
    }

    if (s.du_gibst || s.du_erhaeltst) {
      detailEl.appendChild(h('div', { class: 'io' }, [
        h('div', {}, [h('h4', { text: 'Du gibst' }), h('p', { text: s.du_gibst })]),
        h('div', {}, [h('h4', { text: 'Du erhältst' }), h('p', { text: s.du_erhaeltst })])
      ]));
    }

    if (s.beispielauftrag) {
      detailEl.appendChild(h('div', { class: 'block' }, [
        h('h4', { text: 'So kann dein Auftrag lauten' }),
        h('p', { class: 'example', text: '«' + s.beispielauftrag + '»' })
      ]));
    }

    detailEl.appendChild(h('div', { class: 'block' }, [
      h('h4', { text: 'Das Paket enthält' }),
      h('div', { class: 'files' }, s.dateien.map(function (name) { return h('div', { text: name }); }))
    ]));

    var download = h('a', { class: 'btn', href: s.zip, download: s.id + '.zip' }, [
      downloadIcon(), 'Skill herunterladen (.zip)'
    ]);
    var toggle = h('button', {
      type: 'button',
      class: 'btn btn-outline',
      'aria-expanded': String(state.install),
      text: state.install ? 'Installation ausblenden' : 'Direkt installieren',
      onclick: function () {
        state.install = !state.install;
        render('toggle');
      }
    });
    detailEl.appendChild(h('div', { class: 'actions' }, [download, toggle]));
    detailEl.appendChild(h('p', { class: 'meta', text: 'Zip-Datei, ca. ' + s.groesse_kb + ' KB' }));

    if (state.install) detailEl.appendChild(renderInstall(s));
  }

  function render(focusKey) {
    var skills = visibleSkills();
    var sel = skills.filter(function (s) { return s.id === state.selected; })[0] || skills[0] || null;
    state.selected = sel ? sel.id : null;
    renderChips();
    renderList(skills);
    renderDetail(sel);

    // Fokus nach dem Neuaufbau wiederherstellen, damit die Tastaturbedienung nicht springt
    if (focusKey) {
      var target = null;
      if (focusKey.indexOf('card:') === 0) target = listEl.querySelector('[data-id="' + focusKey.slice(5) + '"]');
      else if (focusKey.indexOf('chip:') === 0) target = chipsEl.querySelector('[data-filter="' + focusKey.slice(5) + '"]');
      else if (focusKey === 'toggle') target = detailEl.querySelector('[aria-expanded]');
      if (target) target.focus({ preventScroll: true });
    }
  }

  fetch('skills.json', { cache: 'no-cache' })
    .then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    })
    .then(function (data) {
      state.data = data;
      var hash = decodeURIComponent(location.hash.replace('#skill-', ''));
      var wanted = data.skills.filter(function (s) { return s.id === hash; })[0];
      state.selected = wanted ? wanted.id : (data.skills[0] && data.skills[0].id);
      render();
    })
    .catch(function () {
      listEl.textContent = '';
      listEl.appendChild(h('p', { class: 'notice', text: 'Die Skills konnten nicht geladen werden. Bitte lade die Seite neu.' }));
    });
})();
