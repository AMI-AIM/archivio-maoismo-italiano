// ============================================================
// DOCUMENTI - Funzionalità delle schede singole
// ============================================================
(function () {
  'use strict';

  // ------------------------------------------------------------
  // UTILITIES CITAZIONI
  // ------------------------------------------------------------
  function getConsultationDate() {
    var now = new Date();
    var year = now.getFullYear();
    var month = String(now.getMonth() + 1).padStart(2, '0');
    var day = String(now.getDate()).padStart(2, '0');
    var iso = year + '-' + month + '-' + day;
    var it = iso;
    try {
      it = new Intl.DateTimeFormat('it-IT', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      }).format(now);
    } catch (e) {
      it = iso;
    }
    return {
      it: it,
      iso: iso
    };
  }

  function safeText(value) {
    if (value === null || value === undefined) {
      return '';
    }
    return String(value);
  }

  // NUOVO: escape HTML per prevenire XSS nei titoli/autori
  function escapeHtml(text) {
    var s = safeText(text);
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function escapeBibtex(value) {
    var text = safeText(value);
    return text
      .replace(/\\/g, '\\textbackslash{}')
      .replace(/([&%#_])/g, '\\$1')
      .replace(/~/g, '\\textasciitilde{}')
      .replace(/\^/g, '\\textasciicircum{}');
  }

  // ------------------------------------------------------------
  // CITAZIONI
  // Norme di riferimento:
  //  - Chicago Manual of Style (notes-bibliography, voce di bibliografia),
  //    adattata all'italiano ("e", "consultato il");
  //  - MLA Handbook, 9a ed. (container: titolo della risorsa, poi
  //    l'archivio come secondo container);
  //  - BibTeX (campi url/urldate supportati da biblatex e natbib);
  //  - "Semplice": tutti gli elementi separati solo da virgole.
  // I nomi in cui il cognome precede il nome (es. cinesi: "Mao Zedong")
  // non vengono invertiti in Chicago e MLA.
  // ------------------------------------------------------------
  var ARCHIVIO_SEP = ', ';

  function authorNames(authors) {
    return (authors || [])
      .map(function (author) {
        return safeText(author.name);
      })
      .filter(Boolean);
  }

  function validAuthors(authors, skipName) {
    return (authors || []).filter(function (a) {
      return a && safeText(a.name) && safeText(a.name) !== skipName;
    });
  }

  // Primo autore: forma invertita "Cognome, Nome" (se nota e se il nome
  // non e' gia' nell'ordine cognome-nome); gli altri in ordine naturale.
  function displayName(author, first) {
    if (author.corporate || !first || author.surname_first) {
      return safeText(author.name);
    }
    return safeText(author.sort_name) || safeText(author.name);
  }

  function joinItalian(list) {
    if (list.length <= 1) {
      return list.join('');
    }
    return list.slice(0, -1).join(', ') + ' e ' + list[list.length - 1];
  }

  function chicagoAuthors(authors) {
    return joinItalian(authors.map(function (a, i) {
      return escapeHtml(displayName(a, i === 0));
    }));
  }

  function mlaAuthors(authors) {
    if (!authors.length) {
      return '';
    }
    var first = escapeHtml(displayName(authors[0], true));
    if (authors.length === 1) {
      return first;
    }
    if (authors.length === 2) {
      var inverted = first.indexOf(',') !== -1;
      return first + (inverted ? ', e ' : ' e ') + escapeHtml(displayName(authors[1], false));
    }
    return first + ', et al';
  }

  function endWithPeriod(text) {
    return /[.!?]$/.test(text) ? text : text + '.';
  }

  // Titolo: corsivo se e' il titolo proprio; tra parentesi quadre e in
  // tondo se e' attribuito dal catalogatore (ISAD 3.1.2).
  function titleHtml(doc) {
    if (doc.title_devised) {
      return '[' + escapeHtml(doc.title) + ']';
    }
    return '<em>' + escapeHtml(doc.title) + '</em>';
  }

  function dateText(doc) {
    return escapeHtml(doc.date_display) || 's.d.';
  }

  function accessText(date) {
    return 'consultato il ' + escapeHtml(date.it);
  }

  function romanToArabic(value) {
    var s = safeText(value).trim().toUpperCase();
    if (/^\d+$/.test(s) || !/^[IVXLCDM]+$/.test(s)) {
      return safeText(value);
    }
    var map = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
    var total = 0;
    for (var i = 0; i < s.length; i++) {
      var cur = map[s[i]];
      var next = map[s[i + 1]] || 0;
      total += cur < next ? -cur : cur;
    }
    return String(total);
  }

  function issueText(doc) {
    var issue = safeText(doc.issue);
    if (!issue) {
      return '';
    }
    var supp = issue.match(/^suppl\.\s*(.+)$/);
    if (supp) {
      return 'suppl. al no. ' + escapeHtml(supp[1]);
    }
    return 'no. ' + escapeHtml(issue);
  }

  function getPeriodicalTitle(doc) {
    return safeText(doc.container_title) || safeText(doc.title);
  }

  // Autori di un periodico: si omette l'ente che coincide con la testata.
  function periodicalAuthors(doc) {
    return validAuthors(doc.authors, getPeriodicalTitle(doc));
  }

  // ---------------- Chicago ----------------
  // Libro:     Cognome, Nome. Titolo. Luogo: Editore, Anno. Archivio, ID.
  //            Consultato il … URL.
  // Fascicolo: Ente. Testata 3, no. 1 (data). Archivio, ID. Consultato il … URL.
  function buildChicago(doc, date) {
    var parts = [];
    var tail = escapeHtml(doc.archive) + ARCHIVIO_SEP + escapeHtml(doc.ami_id) + '. ' +
      'Consultato il ' + escapeHtml(date.it) + '. ' + escapeHtml(doc.url) + '.';

    if (doc.is_periodical) {
      var authorsP = periodicalAuthors(doc);
      if (authorsP.length) {
        parts.push(endWithPeriod(chicagoAuthors(authorsP)));
      }
      var core = '<em>' + escapeHtml(getPeriodicalTitle(doc)) + '</em>';
      var vol = safeText(doc.volume) ? escapeHtml(romanToArabic(doc.volume)) : '';
      var iss = issueText(doc);
      if (vol) {
        core += ' ' + vol + (iss ? ', ' + iss : '');
      } else if (iss) {
        core += ', ' + iss;
      }
      core += ' (' + dateText(doc) + ').';
      parts.push(core);
      parts.push(tail);
      return parts.join(' ');
    }

    var authors = validAuthors(doc.authors);
    if (authors.length) {
      parts.push(endWithPeriod(chicagoAuthors(authors)));
    }
    parts.push(endWithPeriod(titleHtml(doc)));
    var place = safeText(doc.place);
    var publisher = safeText(doc.publisher);
    var pub = '';
    if (place && publisher) {
      pub = escapeHtml(place) + ': ' + escapeHtml(publisher) + ', ';
    } else if (publisher || place) {
      pub = escapeHtml(publisher || place) + ', ';
    }
    parts.push(pub + dateText(doc) + '.');
    parts.push(tail);
    return parts.join(' ');
  }

  // ---------------- MLA (9a ed.) ----------------
  // Libro:     Cognome, Nome. Titolo. Editore, Anno. Archivio, ID, URL.
  //            Consultato il ….
  // Fascicolo: Testata, vol. 3, no. 1, data. Archivio, ID, URL. Consultato il ….
  // Se l'autore coincide con l'editore, MLA lo omette e parte dal titolo.
  function buildMLA(doc, date) {
    var parts = [];
    var tail = '<em>' + escapeHtml(doc.archive) + '</em>, ' + escapeHtml(doc.ami_id) + ', ' +
      escapeHtml(doc.url) + '. Consultato il ' + escapeHtml(date.it) + '.';

    if (doc.is_periodical) {
      var authorsP = periodicalAuthors(doc);
      if (authorsP.length) {
        parts.push(endWithPeriod(mlaAuthors(authorsP)));
      }
      var seg = ['<em>' + escapeHtml(getPeriodicalTitle(doc)) + '</em>'];
      if (safeText(doc.volume)) {
        seg.push('vol. ' + escapeHtml(romanToArabic(doc.volume)));
      }
      if (issueText(doc)) {
        seg.push(issueText(doc));
      }
      seg.push(dateText(doc));
      parts.push(seg.join(', ') + '.');
      parts.push(tail);
      return parts.join(' ');
    }

    var publisher = safeText(doc.publisher);
    var authors = validAuthors(doc.authors);
    if (authors.length === 1 && authors[0].corporate && safeText(authors[0].name) === publisher) {
      authors = [];
    }
    if (authors.length) {
      parts.push(endWithPeriod(mlaAuthors(authors)));
    }
    parts.push(endWithPeriod(titleHtml(doc)));
    parts.push((publisher ? escapeHtml(publisher) + ', ' : '') + dateText(doc) + '.');
    parts.push(tail);
    return parts.join(' ');
  }

  // ---------------- Semplice ----------------
  // Tutti gli elementi separati solo da virgole:
  // Cognome, Nome, Titolo, Luogo, Editore, Data, Archivio, ID, URL, consultato il ….
  function simpleAuthors(authors) {
    return joinItalian(authors.map(function (a, i) {
      return escapeHtml(displayName(a, i === 0));
    }));
  }

  function buildSemplice(doc, date) {
    var el = [];
    if (doc.is_periodical) {
      var authorsP = periodicalAuthors(doc);
      if (authorsP.length) {
        el.push(simpleAuthors(authorsP));
      }
      el.push('<em>' + escapeHtml(getPeriodicalTitle(doc)) + '</em>');
      if (safeText(doc.volume)) {
        el.push('anno ' + escapeHtml(doc.volume));
      }
      if (issueText(doc)) {
        el.push(issueText(doc));
      }
    } else {
      var authors = validAuthors(doc.authors);
      if (authors.length) {
        el.push(simpleAuthors(authors));
      }
      el.push(titleHtml(doc));
      if (safeText(doc.place)) {
        el.push(escapeHtml(doc.place));
      }
      if (safeText(doc.publisher)) {
        el.push(escapeHtml(doc.publisher));
      }
    }
    el.push(dateText(doc));
    el.push(escapeHtml(doc.archive));
    el.push(escapeHtml(doc.ami_id));
    el.push(escapeHtml(doc.url));
    el.push(accessText(date));
    return el.join(', ') + '.';
  }

  // Documenti non bibliografici (foto, volantini, manifesti…): stessa
  // forma della citazione semplice, senza editore.
  function buildMinima(doc, date) {
    var el = [];
    var authors = validAuthors(doc.authors);
    if (authors.length) {
      el.push(simpleAuthors(authors));
    }
    el.push(titleHtml(doc));
    if (safeText(doc.place)) {
      el.push(escapeHtml(doc.place));
    }
    el.push(dateText(doc));
    el.push(escapeHtml(doc.archive));
    el.push(escapeHtml(doc.ami_id));
    el.push(escapeHtml(doc.url));
    el.push(accessText(date));
    return el.join(', ') + '.';
  }

  // ---------------- BibTeX ----------------
  // Persone: "Cognome, Nome"; enti tra graffe singole, cosi' BibTeX non
  // li scompone in nome e cognome: author = {{Renmin Ribao} and {Hongqi}}.
  function bibtexAuthor(author) {
    if (author.corporate) {
      return '{' + escapeBibtex(author.name) + '}';
    }
    return escapeBibtex(safeText(author.sort_name) || safeText(author.name));
  }

  function buildBibtex(doc, date) {
    // MODIFICATO: @book invece di @booklet per opuscoli
    var entryType = '@misc';
    if (doc.type === 'libro' || doc.type === 'opuscolo') {
      entryType = '@book';
    } else if (doc.type === 'articolo') {
      entryType = '@article';
    }
    
    var title = safeText(doc.title);
    if (doc.is_periodical) {
      title = getPeriodicalTitle(doc);
    }
    
    var authors = doc.authors || [];
    
    // Evita duplicati evidenti nei periodici:
    // se l'autore corporativo coincide con la testata, lo omettiamo.
    if (
      doc.is_periodical &&
      authors.length === 1 &&
      authors[0].name === title
    ) {
      authors = [];
    }
    
    var fields = [];
    fields.push('title = {' + escapeBibtex(title) + '}');
    
    if (authors.length) {
      var authorField = authors
        .map(bibtexAuthor)
        .join(' and ');
      fields.push('author = {' + authorField + '}');
    }
    
    if (doc.year) {
      fields.push('year = {' + safeText(doc.year) + '}');
    }
    
    if (doc.is_periodical) {
      if (doc.issue) {
        fields.push('number = {' + escapeBibtex(doc.issue) + '}');
      }
      if (doc.volume) {
        fields.push('volume = {' + escapeBibtex(doc.volume) + '}');
      }
    }
    
    var skipNames = authorNames(doc.authors);
    if (doc.is_periodical) {
      skipNames.push(getPeriodicalTitle(doc));
    }
    
    if (
      doc.publisher &&
      skipNames.indexOf(doc.publisher) === -1
    ) {
      fields.push('publisher = {' + escapeBibtex(doc.publisher) + '}');
    }
    
    if (
      doc.place &&
      skipNames.indexOf(doc.place) === -1 &&
      !doc.is_periodical
    ) {
      fields.push('address = {' + escapeBibtex(doc.place) + '}');
    }
    
    var noteParts = [
      safeText(doc.archive) + ', ' + safeText(doc.ami_id)
    ];
    if (!doc.year) {
      noteParts.push('s.d.');
    }
    if (doc.ia_identifier) {
      noteParts.push('Internet Archive: ' + safeText(doc.ia_identifier));
    }
    
    fields.push('note = {' + escapeBibtex(noteParts.join('; ')) + '}');
    fields.push('url = {' + safeText(doc.url) + '}');
    fields.push('urldate = {' + date.iso + '}');
    
    var lines = [entryType + '{' + safeText(doc.citation_key) + ','];
    fields.forEach(function (field, index) {
      var comma = index < fields.length - 1 ? ',' : '';
      lines.push('  ' + field + comma);
    });
    lines.push('}');
    
    return lines.join('\n');
  }

  function buildCitations(payload) {
    var date = getConsultationDate();
    if (!payload || !payload.doc) {
      return {
        semplice: 'Citazione non disponibile.'
      };
    }
    
    var doc = payload.doc;
    
    if (payload.mode === 'bibliografica') {
      return {
        chicago: buildChicago(doc, date),
        mla: buildMLA(doc, date),
        bibtex: buildBibtex(doc, date),
        semplice: buildSemplice(doc, date)
      };
    }
    
    return {
      semplice: buildMinima(doc, date)
    };
  }

  // ------------------------------------------------------------
  // INIT
  // ------------------------------------------------------------
  function init() {
    var metaBaseUrl = document.querySelector('meta[name="ami-base-url"]');
    var baseUrl = metaBaseUrl
      ? (metaBaseUrl.content || '').replace(/\/$/, '')
      : '';

    function archivioSerieUrl(tag) {
      if (baseUrl) {
        return baseUrl + '/documenti/?serie=' + encodeURIComponent(tag);
      }
      // Le schede documento sono in /documenti/AMI-XXXX/,
      // quindi ../ risolve normalmente all'indice documenti.
      return '../?serie=' + encodeURIComponent(tag);
    }

    // ==========================================================
    // 1. ARGOMENTI: split di serie multiple in link separati
    // ==========================================================
    document.querySelectorAll('.metadata-item').forEach(function (item) {
      var label = item.querySelector('.metadata-label');
      var value = item.querySelector('.metadata-value');
      
      if (!label || !value) {
        return;
      }
      
      if (label.textContent.trim() !== 'Percorsi tematici') {
        return;
      }
      
      var link = value.querySelector('a');
      if (!link) {
        return;
      }
      
      var tags = link.textContent
        .split(';')
        .map(function (t) {
          return t.trim();
        })
        .filter(Boolean);
      
      if (tags.length < 2) {
        return;
      }
      
      var fragment = document.createDocumentFragment();
      tags.forEach(function (tag, index) {
        if (index > 0) {
          fragment.append(', ');
        }
        var a = document.createElement('a');
        a.href = archivioSerieUrl(tag);
        a.textContent = tag;
        fragment.append(a);
      });
      
      value.replaceChildren(fragment);
    });

    // ==========================================================
    // 2. FULLSCREEN iframe
    // ==========================================================
    document.querySelectorAll('.fullscreen-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        var iframe = document.getElementById(this.dataset.target);
        if (!iframe) {
          return;
        }
        var requestFullscreen =
          iframe.requestFullscreen ||
          iframe.webkitRequestFullscreen ||
          iframe.msRequestFullscreen;
        if (requestFullscreen) {
          requestFullscreen.call(iframe);
        }
      });
    });

    // ==========================================================
    // 3. TOGGLE BILINGUE
    // ==========================================================
    document.querySelectorAll('.text-bilingue').forEach(function (section) {
      var buttons = section.querySelectorAll('.lingua-btn');
      var contents = section.querySelectorAll('[data-lingua-content]');
      
      if (!buttons.length || !contents.length) {
        return;
      }
      
      buttons.forEach(function (button) {
        button.addEventListener('click', function () {
          var lingua = this.dataset.lingua;
          buttons.forEach(function (b) {
            b.classList.toggle('lingua-btn--active', b === button);
          });
          contents.forEach(function (content) {
            content.style.display =
              content.dataset.linguaContent === lingua ? '' : 'none';
          });
        });
      });
    });

    // ==========================================================
    // 4. CITAZIONI (MODIFICATO: div invece di textarea, copia avanzata)
    // ==========================================================
    document.querySelectorAll('.citazione-link[data-citazioni-id]').forEach(function (toggleButton) {
      var id = toggleButton.dataset.citazioniId;
      var panel = document.getElementById('citazione-pannello-' + id);
      var textElement = document.getElementById('citazione-testo-' + id);
      var copyButton = document.getElementById('citazione-copia-' + id);
      var dataElement = document.getElementById('citazioni-dati-' + id);
      
      if (!panel || !textElement) {
        return;
      }
      
      var payload = null;
      if (dataElement) {
        try {
          payload = JSON.parse(dataElement.textContent);
        } catch (e) {
          console.warn('Errore parsing citazioni:', e);
        }
      }
      
      var citations = null;
      var hasTabs = Boolean(panel.querySelector('.citazione-tab'));
      var defaultFormat = 'semplice';
      
      if (payload && payload.mode === 'bibliografica' && hasTabs) {
        defaultFormat = 'chicago';
      }
      
      var currentFormat = defaultFormat;
      
      function updateTabs() {
        var tabs = panel.querySelectorAll('.citazione-tab');
        tabs.forEach(function (tab) {
          var active = tab.dataset.formato === currentFormat;
          tab.classList.toggle('citazione-tab--active', active);
          tab.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
      }
      
      function renderFormat() {
        if (!citations) {
          citations = buildCitations(payload);
        }
        // MODIFICATO: innerHTML invece di .value per supportare <em>
        textElement.innerHTML = citations[currentFormat] || citations.semplice || '';
        updateTabs();
      }
      
      var tabs = panel.querySelectorAll('.citazione-tab');
      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          currentFormat = this.dataset.formato;
          if (!citations) {
            citations = buildCitations(payload);
          }
          renderFormat();
        });
      });
      
      function chiudiPannello(ridaiFocus) {
        panel.style.display = 'none';
        toggleButton.setAttribute('aria-expanded', 'false');
        if (ridaiFocus) toggleButton.focus();
      }

      toggleButton.addEventListener('click', function () {
        var isHidden = panel.style.display === 'none' || !panel.style.display;
        if (!isHidden) {
          chiudiPannello(false);
          return;
        }
        // Ricostruisce le citazioni all'apertura, così la data
        // di consultazione è quella del momento effettivo.
        citations = buildCitations(payload);
        renderFormat();
        panel.style.display = '';
        toggleButton.setAttribute('aria-expanded', 'true');
        // Il pannello si apre sotto il visore, spesso fuori schermo: lo si
        // porta in vista e il focus va sul formato attivo (o su Copia).
        var riduci = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        panel.scrollIntoView({ behavior: riduci ? 'auto' : 'smooth', block: 'nearest' });
        var primo = panel.querySelector('.citazione-tab--active') || copyButton;
        if (primo) primo.focus({ preventScroll: true });
      });

      // Esc chiude il pannello e riporta il focus su "Cita questo documento".
      panel.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          e.preventDefault();
          chiudiPannello(true);
        }
      });
      
      if (copyButton) {
        copyButton.setAttribute('aria-live', 'polite');
        copyButton.addEventListener('click', function () {
          if (!textElement.innerHTML) {
            citations = buildCitations(payload);
            renderFormat();
          }
          
          var htmlContent = textElement.innerHTML;
          var plainText = textElement.innerText;
          // Si cambia solo l'etichetta: l'icona SVG nel pulsante resta.
          var etichetta = copyButton.querySelector('.citazione-copia__etichetta') || copyButton;
          var originalText = etichetta.textContent;
          
          function showCopied() {
            etichetta.textContent = 'Copiato';
            copyButton.classList.add('is-copiato');
            setTimeout(function () {
              etichetta.textContent = originalText;
              copyButton.classList.remove('is-copiato');
            }, 1500);
          }
          
          // MODIFICATO: Clipboard API avanzata per copiare sia HTML che Testo Puro
          if (navigator.clipboard && window.ClipboardItem) {
            var htmlBlob = new Blob([htmlContent], { type: 'text/html' });
            var textBlob = new Blob([plainText], { type: 'text/plain' });
            var clipboardItem = new ClipboardItem({
              'text/html': htmlBlob,
              'text/plain': textBlob
            });
            navigator.clipboard.write([clipboardItem])
              .then(showCopied)
              .catch(fallbackCopy);
          } else {
            fallbackCopy();
          }
          
          function fallbackCopy() {
            // Fallback per browser vecchi: seleziona il contenuto del div
            var range = document.createRange();
            range.selectNodeContents(textElement);
            var selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            try {
              document.execCommand('copy');
              showCopied();
            } catch (err) {
              console.error('Copia fallita', err);
            }
            selection.removeAllRanges();
          }
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();