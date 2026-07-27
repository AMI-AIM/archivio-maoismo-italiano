---
title: "Persone"
hide:
  - navigation
  - toc
---

# Persone

<div class="top-row">

    <div class="top-card">
        <a href="mao-zedong/" class="top-card-link">
            <div class="top-card-image-wrapper">
                <img src="/archivio-maoismo-italiano/immagini/profili/mao.png" alt="Mao Zedong" class="top-card-avatar-img" loading="lazy">
            </div>
            <div class="top-card-text">
                <div class="top-card-name">Mao Zedong</div>
                <div class="top-card-dates">1893 – 1976</div>
                <div class="top-card-count">18 documenti</div>
            </div>
        </a>
    </div>

    <div class="top-card">
        <a href="osvaldo-pesce/" class="top-card-link">
            <div class="top-card-image-wrapper">
                <img src="data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
    <rect width="100" height="100" fill="#6e6217"/>
    <text x="50" y="55" font-family="Arial, sans-serif" font-size="32" font-weight="600" fill="white" text-anchor="middle" dominant-baseline="central">OP</text>
</svg>" alt="Osvaldo Pesce" class="top-card-avatar-img" loading="lazy">
            </div>
            <div class="top-card-text">
                <div class="top-card-name">Osvaldo Pesce</div>
                <div class="top-card-dates">193? – 2021</div>
                <div class="top-card-count">5 documenti</div>
            </div>
        </a>
    </div>

    <div class="top-card">
        <a href="dino-dini/" class="top-card-link">
            <div class="top-card-image-wrapper">
                <img src="data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
    <rect width="100" height="100" fill="#362a8f"/>
    <text x="50" y="55" font-family="Arial, sans-serif" font-size="32" font-weight="600" fill="white" text-anchor="middle" dominant-baseline="central">DD</text>
</svg>" alt="Dino Dini" class="top-card-avatar-img" loading="lazy">
            </div>
            <div class="top-card-text">
                <div class="top-card-name">Dino Dini</div>
                <div class="top-card-dates"></div>
                <div class="top-card-count">3 documenti</div>
            </div>
        </a>
    </div>
</div>
<div class="people-grid">

<div class="people-card">
    <a href="chen-boda/" class="people-link">
        <div class="people-name">Chen Boda</div>
        <div class="people-dates">1904 – 1989</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="fosco-dinucci/" class="people-link">
        <div class="people-name">Fosco Dinucci</div>
        <div class="people-dates">1921 – 1993</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="jiang-qing/" class="people-link">
        <div class="people-name">Jiang Qing</div>
        <div class="people-dates">1914 – 1991</div>
        <div class="people-count">1 documento</div>
    </a>
</div>

<div class="people-card">
    <a href="kang-sheng/" class="people-link">
        <div class="people-name">Kang Sheng</div>
        <div class="people-dates">1898 – 1975</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="lin-biao/" class="people-link">
        <div class="people-name">Lin Biao</div>
        <div class="people-dates">1907 – 1971</div>
        <div class="people-count">1 documento</div>
    </a>
</div>

<div class="people-card">
    <a href="roberto-sassi/" class="people-link">
        <div class="people-name">Roberto Sassi</div>
        <div class="people-dates">1960 – 2023</div>
        <div class="people-count">1 documento</div>
    </a>
</div>

<div class="people-card">
    <a href="vincenzo-calo/" class="people-link">
        <div class="people-name">Vincenzo Calò</div>
        <div class="people-dates"></div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="yao-wenyuan/" class="people-link">
        <div class="people-name">Yao Wenyuan</div>
        <div class="people-dates">1931 – 2005</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="zhou-enlai/" class="people-link">
        <div class="people-name">Zhou Enlai</div>
        <div class="people-dates">1898 – 1976</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>
</div>

<style>
/* ============================================================
   TOP ROW - Card quadrate, immagine a pieno campo, testo in basso
   ============================================================ */
.top-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}

.top-card {
    aspect-ratio: 1 / 1;
    background: var(--md-code-bg-color);
    border-radius: 12px;
    border: 1px solid var(--md-default-fg-color--lightest);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}

.top-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}

.top-card-link {
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.top-card-image-wrapper {
    flex: 1;
    overflow: hidden;
    background: var(--md-code-bg-color);
    display: flex;
    align-items: center;
    justify-content: center;
}

.top-card-avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.top-card-text {
    padding: 0.6rem 1rem 0.8rem 1rem;
    background: var(--md-code-bg-color);
    border-top: 1px solid var(--md-default-fg-color--lightest);
    flex-shrink: 0;
}

.top-card-name {
    font-size: 1rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.2;
}

.top-card-dates {
    font-size: 0.8rem;
    color: var(--md-default-fg-color--light);
}

.top-card-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
    font-weight: 400;
}

/* ============================================================
   LISTA STANDARD (ordinata alfabeticamente)
   ============================================================ */
.people-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1rem;
}

.people-card {
    background: var(--md-code-bg-color);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    transition: background-color 0.2s, transform 0.15s, box-shadow 0.2s;
    border: 1px solid var(--md-default-fg-color--lightest);
    min-height: 80px;
    display: flex;
    align-items: center;
}

.people-card:hover {
    background: var(--md-default-bg-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.people-link {
    text-decoration: none;
    display: flex;
    flex-direction: column;
    width: 100%;
    gap: 0.05rem;
}

.people-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
}

.people-dates {
    font-size: 0.7rem;
    color: var(--md-default-fg-color--light);
}

.people-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 900px) {
    .people-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .top-row {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    .top-card {
        aspect-ratio: auto;
        min-height: 200px;
    }
    .top-card-text {
        padding: 0.4rem 0.8rem 0.6rem 0.8rem;
    }
    .top-card-name {
        font-size: 0.95rem;
    }
}

@media (max-width: 600px) {
    .people-grid {
        grid-template-columns: 1fr;
    }
    .people-name {
        font-size: 0.9rem;
    }
    .people-dates {
        font-size: 0.65rem;
    }
}
</style>
