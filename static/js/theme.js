/* ════════════════════════════════════════════════════════════
   HalalTracker — Theme Manager
   Kun/tun rejimini boshqaradi: tizim sozlamasini aniqlash,
   qo'lda almashtirish, saqlab qolish (localStorage) va
   tizim mavzusi o'zgarganda jonli moslashish.

   Eslatma: FOUC (mavzu "miltillashi")ning oldini olish uchun
   index.html <head> boshida kichik inline skript bor — u
   data-theme atributini CSS yuklanishidan oldin o'rnatadi.
   Bu fayl esa keyinroq tugma va meta theme-color'ni bog'laydi.
   ════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var STORAGE_KEY = 'halaltracker-theme'; // 'light' | 'dark' | (yo'q bo'lsa — avtomatik)
    var root = document.documentElement;
    var media = window.matchMedia('(prefers-color-scheme: dark)');
    var THEME_COLORS = { light: '#eef2ee', dark: '#090d0b' };

    function systemTheme() {
        return media.matches ? 'dark' : 'light';
    }

    function savedPreference() {
        try {
            return localStorage.getItem(STORAGE_KEY); // null = "tizimga ergashish"
        } catch (e) {
            return null;
        }
    }

    function resolveTheme() {
        return savedPreference() || systemTheme();
    }

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', THEME_COLORS[theme] || THEME_COLORS.light);
    }

    function toggle() {
        var next = resolveTheme() === 'dark' ? 'light' : 'dark';
        try {
            localStorage.setItem(STORAGE_KEY, next);
        } catch (e) { /* localStorage yo'q bo'lsa ham UI ishlashda davom etadi */ }
        applyTheme(next);
    }

    // Foydalanuvchi hali qo'lda tanlamagan bo'lsa, tizim mavzusi
    // o'zgarganda (masalan kechqurun avtomatik tun rejimiga o'tganda)
    // ilova ham jonli ravishda moslashadi.
    if (media.addEventListener) {
        media.addEventListener('change', function () {
            if (!savedPreference()) applyTheme(systemTheme());
        });
    }

    // <head> dagi inline skript mavzuni allaqachon qo'ygan,
    // bu yerda faqat meta theme-color'ni sinxronlaymiz.
    applyTheme(resolveTheme());

    window.ThemeManager = {
        toggle: toggle,
        resolveTheme: resolveTheme
    };
})();

