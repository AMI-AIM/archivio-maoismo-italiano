---
title: "Persone"
hide:
  - navigation
  - toc
---

# Persone

<div class="people-grid">

<div class="people-card">
    <a href="chen-boda/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Chen Boda</div>
        <div class="people-dates">1904 – 1989</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="dino-dini/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Dino Dini</div>
        
        <div class="people-count">3 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="fosco-dinucci/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Fosco Dinucci</div>
        <div class="people-dates">1921 – 1993</div>
        <div class="people-count">2 documenti</div>
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

<div class="people-card">
    <a href="kang-sheng/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Kang Sheng</div>
        <div class="people-dates">1898 – 1975</div>
        <div class="people-count">2 documenti</div>
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
    <a href="mao-zedong/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Mao Zedong</div>
        <div class="people-dates">1893 – 1976</div>
        <div class="people-count">18 documenti</div>
    </a>
</div>

<div class="people-card">
    <a href="osvaldo-pesce/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Osvaldo Pesce</div>
        <div class="people-dates">193? – 2021</div>
        <div class="people-count">5 documenti</div>
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
    <a href="vincenzo-calo/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Vincenzo Calò</div>
        
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
    <a href="zhou-enlai/" class="people-link">
        <div class="people-tipo">Persona</div>
        <div class="people-name">Zhou Enlai</div>
        <div class="people-dates">1898 – 1976</div>
        <div class="people-count">2 documenti</div>
    </a>
</div>

</div>

<style>
.people-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
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
