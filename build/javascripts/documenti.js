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

  function authorNames(authors) {
    return (authors || [])
      .map(function (author) {
        return safeText(author.name);
      })
      .filter(Boolean);
  }

  function buildAuthorPart(authors, skipName) {
    var names = authorNames(authors).filter(function (name) {
      return name !== skipName;
    });
    if (!names.length) {
      return '';
    }
    return escapeHtml(names.join('; ')) + '. ';
  }

  function buildArchivePart(doc) {
    return escapeHtml(doc.archive) + ' (' + escapeHtml(doc.ami_id) + ')';
  }

  function buildAccessPart(date) {
    return 'Data di consultazione: ' + escapeHtml(date.it) + '.';
  }

  function buildPublisherPartChicago(doc) {
    var place = safeText(doc.place);
    var publisher = safeText(doc.publisher);
    if (place && publisher) {
      return escapeHtml(place) + ': ' + escapeHtml(publisher) + ', ';
    }
    if (publisher) {
      return escapeHtml(publisher) + ', ';
    }
    if (place) {
      return escapeHtml(place) + ', ';
    }
    return '';
  }

  function buildPeriodicalParts(doc) {
    var parts = [];
    if (doc.volume) {
      parts.push('anno ' + escapeHtml(doc.volume));
    }
    if (doc.issue) {
      parts.push('no. ' + escapeHtml(doc.issue));
    }
    return parts;
  }

  function getPeriodicalTitle(doc) {
    return safeText(doc.container_title) || safeText(doc.title);
  }

  function buildChicago(doc, date) {
    var access = buildAccessPart(date);
    var archive = buildArchivePart(doc);
    
    if (doc.is_periodical) {
      var journal = getPeriodicalTitle(doc);
      var authorPart = buildAuthorPart(doc.authors, journal);
      var parts = buildPeriodicalParts(doc);
      var core = authorPart + '<em>' + escapeHtml(journal) + '</em>';
      if (parts.length) {
        core += ', ' + parts.join(', ');
      }
      core += ', ' + (escapeHtml(doc.date_display) || 's.d.') + '.';
      return core + ' ' + archive + '. ' + escapeHtml(doc.url) + '. ' + access;
    }
    
    var author = buildAuthorPart(doc.authors);
    var publisher = buildPublisherPartChicago(doc);
    return (
      author +
      '<em>' + escapeHtml(doc.title) + '</em>. ' +
      publisher +
      (escapeHtml(doc.date_display) || 's.d.') + '. ' +
      archive + '. ' +
      escapeHtml(doc.url) + '. ' +
      access
    );
  }

  function buildMLA(doc, date) {
    var access = buildAccessPart(date);
    var archive = buildArchivePart(doc);
    
    if (doc.is_periodical) {
      var journal = getPeriodicalTitle(doc);
      var authorPart = buildAuthorPart(doc.authors, journal);
      var parts = buildPeriodicalParts(doc);
      var core = authorPart + '<em>' + escapeHtml(journal) + '</em>';
      if (parts.length) {
        core += ', ' + parts.join(', ');
      }
      core += ', ' + (escapeHtml(doc.date_display) || 's.d.') + '.';
      return core + ' ' + archive + ', ' + escapeHtml(doc.url) + '. ' + access;
    }
    
    var author = buildAuthorPart(doc.authors);
    var publisher = safeText(doc.publisher) || safeText(doc.place);
    if (publisher) {
      publisher = escapeHtml(publisher) + ', ';
    } else {
      publisher = '';
    }
    return (
      author +
      '<em>' + escapeHtml(doc.title) + '</em>. ' +
      publisher +
      (escapeHtml(doc.date_display) || 's.d.') + '. ' +
      archive + ', ' +
      escapeHtml(doc.url) + '. ' +
      access
    );
  }

  function buildSemplice(doc, date) {
    var access = buildAccessPart(date);
    var archive = buildArchivePart(doc);
    
    if (doc.is_periodical) {
      var journal = getPeriodicalTitle(doc);
      var parts = buildPeriodicalParts(doc);
      var core = '<em>' + escapeHtml(journal) + '</em>';
      if (parts.length) {
        core += ', ' + parts.join(', ');
      }
      core += ' (' + (escapeHtml(doc.date_display) || 's.d.') + ')';
      var author = buildAuthorPart(doc.authors, journal).replace(/\.\s*$/, '');
      if (author) {
        core += '. ' + author;
      }
      return core + '. ' + archive + '. ' + escapeHtml(doc.url) + '. ' + access;
    }
    
    var author = buildAuthorPart(doc.authors).replace(/\.\s*$/, '');
    var details = [];
    if (doc.place && doc.publisher) {
      details.push(escapeHtml(doc.place) + ': ' + escapeHtml(doc.publisher));
    } else if (doc.publisher) {
      details.push(escapeHtml(doc.publisher));
    } else if (doc.place) {
      details.push(escapeHtml(doc.place));
    }
    
    var text = '';
    if (author) {
      text += author + ', ';
    }
    text += '<em>' + escapeHtml(doc.title) + '</em>';
    if (details.length) {
      text += ', ' + details.join(', ');
    }
    text += ', ' + (escapeHtml(doc.date_display) || 's.d.');
    return text + '. ' + archive + '. ' + escapeHtml(doc.url) + '. ' + access;
  }

  function buildMinima(doc, date) {
    var access = buildAccessPart(date);
    var archive = buildArchivePart(doc);
    return (
      '<em>' + escapeHtml(doc.title) + '</em>, ' +
      (escapeHtml(doc.date_display) || 's.d.') + '. ' +
      archive + '. ' +
      escapeHtml(doc.url) + '. ' +
      access
    );
  }

  function bibtexAuthor(author) {
    var name = escapeBibtex(author.name);
    if (author.corporate) {
      return '{{' + name + '}}';
    }
    return name;
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
      
      if (label.textContent.trim() !== 'Argomenti') {
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
          tab.setAttribute('aria-selected', active ? 'true' : 'false');
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
      
      toggleButton.addEventListener('click', function () {
        var isHidden = panel.style.display === 'none' || !panel.style.display;
        if (isHidden) {
          // Ricostruisce le citazioni all'apertura, così la data
          // di consultazione è quella del momento effettivo.
          citations = buildCitations(payload);
          renderFormat();
        }
        panel.style.display = isHidden ? '' : 'none';
        toggleButton.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
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
          var originalText = copyButton.textContent;
          
          function showCopied() {
            copyButton.textContent = '✅ Copiato!';
            setTimeout(function () {
              copyButton.textContent = originalText;
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