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
            <div class="top-card-avatar" style="background-color: #882876;"><span class="top-card-initials">MZ</span></div>
            <div class="top-card-name">Mao Zedong</div>
            <div class="top-card-dates">1893 – 1976</div>
            <div class="top-card-count">18 documenti</div>
        </a>
    </div>

    <div class="top-card">
        <a href="osvaldo-pesce/" class="top-card-link">
            <div class="top-card-avatar" style="background-color: #6e6217;"><span class="top-card-initials">OP</span></div>
            <div class="top-card-name">Osvaldo Pesce</div>
            <div class="top-card-dates">193? – 2021</div>
            <div class="top-card-count">5 documenti</div>
        </a>
    </div>

    <div class="top-card">
        <a href="dino-dini/" class="top-card-link">
            <div class="top-card-avatar" style="background-color: #362a8f;"><span class="top-card-initials">DD</span></div>
            <div class="top-card-name">Dino Dini</div>
            <div class="top-card-dates"></div>
            <div class="top-card-count">3 documenti</div>
        </a>
    </div>
</div>
<div class="people-grid">

<div class="people-card">
    <a href="fosco-dinucci/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Fosco Dinucci</div>
        <div class="people-dates">1921 – 1993</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="yao-wenyuan/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Yao Wenyuan</div>
        <div class="people-dates">1931 – 2005</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="vincenzo-calo/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Vincenzo Calò</div>
        <div class="people-dates"></div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="kang-sheng/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Kang Sheng</div>
        <div class="people-dates">1898 – 1975</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="zhou-enlai/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Zhou Enlai</div>
        <div class="people-dates">1898 – 1976</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="chen-boda/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Chen Boda</div>
        <div class="people-dates">1904 – 1989</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="roberto-sassi/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Roberto Sassi</div>
        <div class="people-dates">1960 – 2023</div>
        <div class="people-count">1 documento</div>
    </a>
</div>

<div class="people-card">
    <a href="lin-biao/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Lin Biao</div>
        <div class="people-dates">1907 – 1971</div>
        <div class="people-count">1 documento</div>
    </a>
</div>

<div class="people-card">
    <a href="jiang-qing/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Jiang Qing</div>
        <div class="people-dates">1914 – 1991</div>
        <div class="people-count">1 documento</div>
    </a>
</div>
</div>

<style>
/* ============================================================
   TOP ROW
   ============================================================ */
.top-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-bottom: 2.5rem;
}

.top-card {
    background: var(--md-code-bg-color);
    border-radius: 12px;
    border: 1px solid var(--md-default-fg-color--lightest);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    text-align: center;
    padding: 1.5rem 0.5rem;
    min-height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
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
    align-items: center;
    gap: 0.5rem;
    width: 100%;
}

.top-card-avatar {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.top-card-avatar-img {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
}

.top-card-initials {
    font-size: 2.2rem;
    font-weight: 600;
    color: #ffffff;
    text-shadow: 0 1px 4px rgba(0,0,0,0.2);
    text-transform: uppercase;
}

.top-card-name {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
}

.top-card-dates {
    font-size: 0.85rem;
    color: var(--md-default-fg-color--light);
}

.top-card-count {
    font-size: 0.75rem;
    font-weight: 600;
    color: #ffffff !important;
    background: var(--md-primary-fg-color);
    padding: 0.15rem 0.8rem;
    border-radius: 20px;
    display: inline-block;
}

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
    min-height: 100px;
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
    gap: 0.1rem;
}

.people-tipo {
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ffffff !important;
    background: var(--md-primary-fg-color);
    padding: 0.05rem 0.6rem;
    border-radius: 4px;
    display: inline-block;
    width: fit-content;
}

.people-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    line-height: 1.3;
    word-break: break-word;
}

.people-dates {
    font-size: 0.7rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.05rem;
}

.people-count {
    font-size: 0.75rem;
    color: var(--md-default-fg-color--light);
    margin-top: 0.1rem;
}

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
        min-height: 180px;
        padding: 1rem 0.5rem;
    }
    .top-card-avatar,
    .top-card-avatar-img {
        width: 70px;
        height: 70px;
    }
    .top-card-initials {
        font-size: 1.8rem;
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
