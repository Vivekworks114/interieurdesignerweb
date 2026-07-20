(function () {
  // Fill footer year
  var year = String(new Date().getFullYear());
  document.querySelectorAll('.current-year').forEach(function (el) {
    el.textContent = year;
  });

  // Elementor Pro nav: submenu carets
  document.querySelectorAll('.elementor-nav-menu .menu-item-has-children > a').forEach(function (link) {
    if (link.querySelector('.sub-arrow')) return;
    var arrow = document.createElement('span');
    arrow.className = 'sub-arrow';
    arrow.innerHTML = '<i class="fas fa-caret-down" aria-hidden="true"></i>';
    link.appendChild(arrow);
  });

  function closeAllMenus(except) {
    document.querySelectorAll('.elementor-menu-toggle.elementor-active').forEach(function (toggle) {
      if (except && toggle === except) return;
      toggle.classList.remove('elementor-active');
      toggle.setAttribute('aria-expanded', 'false');
      var dropdown = toggle.nextElementSibling;
      if (dropdown && dropdown.classList.contains('elementor-nav-menu__container')) {
        dropdown.setAttribute('aria-hidden', 'true');
      }
    });
  }

  function closeDesktopHighlights(except) {
    document.querySelectorAll('.elementor-nav-menu--main .menu-item.highlighted').forEach(function (item) {
      if (except && item === except) return;
      item.classList.remove('highlighted');
    });
  }

  document.querySelectorAll('.elementor-nav-menu--main .menu-item-has-children').forEach(function (item) {
    var link = item.querySelector(':scope > a');
    if (!link) return;

    item.addEventListener('mouseenter', function () {
      if (!window.matchMedia('(min-width: 1025px)').matches) return;
      closeDesktopHighlights(item);
      item.classList.add('highlighted');
    });

    item.addEventListener('mouseleave', function () {
      if (!window.matchMedia('(min-width: 1025px)').matches) return;
      item.classList.remove('highlighted');
    });

    link.addEventListener('click', function (event) {
      if (!window.matchMedia('(min-width: 1025px)').matches) return;
      if (!item.classList.contains('highlighted')) {
        event.preventDefault();
        closeDesktopHighlights(item);
        item.classList.add('highlighted');
      }
    });
  });

  document.querySelectorAll('.elementor-nav-menu--toggle').forEach(function (widget) {
    var toggle = widget.querySelector('.elementor-menu-toggle');
    if (!toggle) return;
    var dropdown =
      toggle.nextElementSibling &&
      toggle.nextElementSibling.classList.contains('elementor-nav-menu__container')
        ? toggle.nextElementSibling
        : null;
    if (!dropdown) return;

    var open = function () {
      closeAllMenus(toggle);
      toggle.classList.add('elementor-active');
      toggle.setAttribute('aria-expanded', 'true');
      dropdown.setAttribute('aria-hidden', 'false');
    };
    var close = function () {
      toggle.classList.remove('elementor-active');
      toggle.setAttribute('aria-expanded', 'false');
      dropdown.setAttribute('aria-hidden', 'true');
    };
    var onToggle = function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (toggle.classList.contains('elementor-active')) close();
      else open();
    };
    toggle.addEventListener('click', onToggle);
    toggle.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') onToggle(event);
    });
  });

  document.querySelectorAll('.elementor-nav-menu--dropdown .menu-item-has-children > a').forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (window.matchMedia('(min-width: 1025px)').matches) return;
      var parent = link.parentElement;
      var submenu = parent && parent.querySelector(':scope > .sub-menu');
      if (!submenu) return;
      event.preventDefault();
      parent.classList.toggle('elementor-active');
    });
  });

  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!(target instanceof Element)) return;
    if (target.closest('.elementor-nav-menu--toggle')) return;
    if (target.closest('.elementor-nav-menu--main .menu-item-has-children')) return;
    closeAllMenus();
    closeDesktopHighlights();
  });

  // Accordion FAQ
  document.querySelectorAll('.elementor-accordion').forEach(function (accordion) {
    accordion.querySelectorAll('.elementor-accordion-item').forEach(function (item) {
      var title = item.querySelector('.elementor-tab-title');
      var content = item.querySelector('.elementor-tab-content');
      if (!title || !content) return;

      title.setAttribute('aria-expanded', 'false');
      title.classList.remove('elementor-active');
      content.style.display = 'none';
      content.classList.remove('elementor-active');

      title.addEventListener('click', function (event) {
        event.preventDefault();
        var isOpen = title.classList.contains('elementor-active');

        // close siblings
        accordion.querySelectorAll('.elementor-accordion-item').forEach(function (other) {
          var t = other.querySelector('.elementor-tab-title');
          var c = other.querySelector('.elementor-tab-content');
          if (!t || !c) return;
          t.classList.remove('elementor-active');
          t.setAttribute('aria-expanded', 'false');
          c.classList.remove('elementor-active');
          c.style.display = 'none';
        });

        if (!isOpen) {
          title.classList.add('elementor-active');
          title.setAttribute('aria-expanded', 'true');
          content.classList.add('elementor-active');
          content.style.display = 'block';
        }
      });
    });
  });

  // Table of contents — mirror Elementor Pro TOC DOM
  document.querySelectorAll('.elementor-toc__body').forEach(function (body) {
    var widget = body.closest('.elementor-widget-table-of-contents');
    var settings = {};
    try {
      settings = JSON.parse((widget && widget.getAttribute('data-settings')) || '{}');
    } catch (e) {}
    var tags = (settings.headings_by_tags || ['h2', 'h3']).join(',');
    var root = document.getElementById('content') || body.closest('.elementor') || document.body;
    var headings = Array.prototype.slice.call(root.querySelectorAll(tags)).filter(function (h) {
      return !h.closest('.elementor-toc') && !h.closest('.elementor-accordion') && !h.closest('[data-elementor-type="footer"]') && !h.closest('[data-elementor-type="header"]');
    });
    if (!headings.length) return;

    var list = document.createElement('ul');
    list.className = 'elementor-toc__list-wrapper';

    headings.forEach(function (heading, index) {
      var anchorId = 'elementor-toc__heading-anchor-' + index;
      heading.id = anchorId;

      var item = document.createElement('li');
      item.className = 'elementor-toc__list-item';

      var wrapper = document.createElement('div');
      wrapper.className = 'elementor-toc__list-item-text-wrapper';

      var icon = document.createElement('i');
      icon.className = 'fas fa-circle';
      icon.setAttribute('aria-hidden', 'true');
      wrapper.appendChild(icon);

      var link = document.createElement('a');
      link.href = '#' + anchorId;
      link.textContent = (heading.textContent || '').trim();
      wrapper.appendChild(link);

      item.appendChild(wrapper);
      list.appendChild(item);
    });

    var spinner = body.querySelector('.elementor-toc__spinner-container');
    if (spinner) spinner.remove();
    body.innerHTML = '';
    body.appendChild(list);
  });

  document.querySelectorAll('.elementor-toc__header').forEach(function (header) {
    header.addEventListener('click', function () {
      var widget = header.closest('.elementor-widget-table-of-contents');
      if (!widget) return;
      widget.classList.toggle('elementor-toc--minimized');
    });
  });

  // Elementor Posts: apply item-ratio class only when widget ::after exposes a ratio
  document.querySelectorAll('.elementor-widget-posts, .elementor-widget-archive-posts').forEach(function (widget) {
    var after = window.getComputedStyle(widget, ':after').getPropertyValue('content');
    if (!after || after === 'none' || after === 'normal') return;
    var ratio = after.replace(/['"]/g, '').trim();
    if (!ratio || ratio === '0') return;
    var container = widget.querySelector('.elementor-posts-container');
    if (container) container.classList.add('elementor-has-item-ratio');
  });

  // Resolve lazy-loaded images without Elementor/LiteSpeed JS
  document.querySelectorAll('img[data-lazy-src], img[data-src], img[data-litespeed-src]').forEach(function (img) {
    var real =
      img.getAttribute('data-lazy-src') ||
      img.getAttribute('data-src') ||
      img.getAttribute('data-litespeed-src');
    if (!real) return;
    var current = img.getAttribute('src') || '';
    if (!current || current.indexOf('data:image') === 0 || current.indexOf('placeholder') !== -1) {
      img.setAttribute('src', real);
    }
  });
})();
