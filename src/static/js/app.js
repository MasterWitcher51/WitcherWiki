/**
 * The Witcher 3: Wild Hunt - Bestiary Compendium & Alchemy Lab
 * Enhanced with Fuse.js (Fuzzy Search) & Tippy.js (Runic Tooltips)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  let allMonsters = [];
  let filteredMonsters = [];
  let allRecipes = [];
  let filteredRecipes = [];
  
  let activeClass = "all";
  let activeSign = null;
  let searchQuery = "";
  let activeAlchemyType = "all";
  let alchemySearchQuery = "";

  // Fuse.js Index Instances
  let monsterFuse = null;
  let alchemyFuse = null;

  // DOM Elements - Bestiary
  const grid = document.getElementById("monsters-grid");
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const resultsCount = document.getElementById("results-count");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");

  // Stats DOM
  const statTotalMonsters = document.getElementById("stat-total-monsters");
  const statTotalClasses = document.getElementById("stat-total-classes");
  const statTotalAlchemy = document.getElementById("stat-total-alchemy");
  const statTotalLoot = document.getElementById("stat-total-loot");

  // Modals DOM
  const dossierModal = document.getElementById("dossier-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const combatPrepModal = document.getElementById("combat-prep-modal");
  const prepModalCloseBtn = document.getElementById("prep-modal-close-btn");
  const prepMonsterSelect = document.getElementById("prep-monster-select");
  const prepResultDisplay = document.getElementById("prep-result-display");

  // Alchemy Modal DOM
  const alchemyModal = document.getElementById("alchemy-modal");
  const alchemyModalCloseBtn = document.getElementById("alchemy-modal-close-btn");
  const alchemySearchInput = document.getElementById("alchemy-search-input");
  const alchemyRecipesGrid = document.getElementById("alchemy-recipes-grid");
  const alchemyResultsInfo = document.getElementById("alchemy-results-info");

  // Header Buttons
  const randomBtn = document.getElementById("random-btn");
  const prepModeBtn = document.getElementById("prep-mode-btn");
  const alchemyBtn = document.getElementById("alchemy-btn");

  // Sign Lore Tooltip Dictionary
  const SIGN_TOOLTIPS = {
    igni: "<strong>🔥 Igni</strong><br>Projects a cone of fire that scorches opponents and inflicts continuous burning.",
    quen: "<strong>🛡️ Quen</strong><br>Forms a protective energy shield absorbing physical attacks and magical strikes.",
    aard: "<strong>💨 Aard</strong><br>Telekinetic blast capable of staggering or knocking flying and heavy beasts to the ground.",
    axii: "<strong>💫 Axii</strong><br>Mental charm that confuses and stuns foes, lowering beast aggression.",
    yrden: "<strong>🔮 Yrden</strong><br>Magical floor glyph slowing enemies and forcing ethereal Specters into corporeal form.",
    oil: "<strong>🧪 Blade Oils</strong><br>Coats silver and steel swords with toxic decoctions to deal +50% bonus damage.",
    bomb: "<strong>💣 Bombs</strong><br>Alchemical explosives like Northern Wind (freeze), Moon Dust (anti-transform), or Dimeritium."
  };

  // -------------------------------------------------------------
  // 1. Fetch & Initialize Data
  // -------------------------------------------------------------
  async function init() {
    try {
      const [monstersRes, statsRes, alchemyRes] = await Promise.all([
        fetch("/api/monsters"),
        fetch("/api/stats"),
        fetch("/api/alchemy")
      ]);

      const monstersData = await monstersRes.json();
      const statsData = await statsRes.json();
      const alchemyData = await alchemyRes.json();

      allMonsters = monstersData.monsters || [];
      filteredMonsters = [...allMonsters];

      allRecipes = alchemyData.recipes || [];
      filteredRecipes = [...allRecipes];

      // Initialize Fuse.js for typo-tolerant fuzzy search
      initFuzzySearch();

      updateStats(statsData);
      populatePrepSelect();
      renderMonsters();
      renderAlchemyRecipes();
      initSignTooltips();
      setupEventListeners();
    } catch (err) {
      console.error("Failed to load bestiary & alchemy archives:", err);
      grid.innerHTML = `
        <div class="empty-state">
          <p>⚠️ Failed to load Bestiary archives from the server.</p>
        </div>
      `;
    }
  }

  function initFuzzySearch() {
    if (typeof Fuse !== "undefined") {
      monsterFuse = new Fuse(allMonsters, {
        keys: [
          { name: "Name", weight: 0.4 },
          { name: "Class", weight: 0.2 },
          { name: "Location", weight: 0.15 },
          { name: "Weaknesses", weight: 0.15 },
          { name: "Loot", weight: 0.1 }
        ],
        threshold: 0.35, // Balanced fuzzy tolerance for typos like "grifn" -> "Griffin"
        ignoreLocation: true
      });

      alchemyFuse = new Fuse(allRecipes, {
        keys: [
          { name: "name", weight: 0.4 },
          { name: "effect", weight: 0.3 },
          { name: "monster_ingredient", weight: 0.2 },
          { name: "target_monsters", weight: 0.1 }
        ],
        threshold: 0.35,
        ignoreLocation: true
      });
    }
  }

  function updateStats(stats) {
    if (statTotalMonsters) statTotalMonsters.textContent = stats.total_monsters || allMonsters.length;
    if (statTotalClasses) statTotalClasses.textContent = stats.total_classes || 12;
    if (statTotalAlchemy) statTotalAlchemy.textContent = stats.total_alchemy_recipes || allRecipes.length;
    if (statTotalLoot) statTotalLoot.textContent = stats.total_loot_types || 0;
  }

  function populatePrepSelect() {
    if (!prepMonsterSelect) return;
    const sorted = [...allMonsters].sort((a, b) => a.Name.localeCompare(b.Name));
    sorted.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.Name;
      opt.textContent = `${m.Name} (${m.Class || "Unknown"})`;
      prepMonsterSelect.appendChild(opt);
    });
  }

  // -------------------------------------------------------------
  // 2. Render Cards & Grid
  // -------------------------------------------------------------
  function renderMonsters() {
    if (filteredMonsters.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📜</div>
          <h3>No creatures found</h3>
          <p>No bestiary records match your current criteria on the Path.</p>
        </div>
      `;
      resultsCount.textContent = `Showing 0 monsters`;
      updateResetButtonVisibility();
      return;
    }

    resultsCount.textContent = `Showing ${filteredMonsters.length} of ${allMonsters.length} monsters`;
    updateResetButtonVisibility();

    grid.innerHTML = filteredMonsters.map(m => createMonsterCardHtml(m)).join("");

    // Attach card click events
    grid.querySelectorAll(".monster-card").forEach(card => {
      card.addEventListener("click", () => {
        const monsterName = card.dataset.name;
        const monster = allMonsters.find(m => m.Name === monsterName);
        if (monster) openDossier(monster);
      });
    });

    // Reinitialize tooltips on the newly rendered cards
    initCardTooltips();
  }

  function createMonsterCardHtml(m) {
    const weaknesses = m.Weaknesses || [];
    const loot = (m.Loot || []).filter(item => !item.startsWith("None ("));
    
    // Weakness preview badges (max 3)
    const weaknessBadges = weaknesses.slice(0, 3).map(w => {
      const pillClass = getWeaknessBadgeClass(w);
      return `<span class="badge-pill ${pillClass}">${escapeHtml(w)}</span>`;
    }).join("");
    
    const moreWeakness = weaknesses.length > 3 
      ? `<span class="badge-pill">+${weaknesses.length - 3}</span>` 
      : "";

    // Loot preview badges (max 2) - check if item has alchemy recipe
    const lootBadges = loot.slice(0, 2).map(item => {
      const recipe = findRecipeForIngredient(item);
      const recipeClass = recipe ? "has-recipe" : "";
      const icon = recipe ? "⚗️ " : "";
      return `<span class="badge-pill loot-pill ${recipeClass}" data-ingredient="${escapeHtml(item)}">${icon}${escapeHtml(item)}</span>`;
    }).join("");

    const moreLoot = loot.length > 2 
      ? `<span class="badge-pill loot-pill">+${loot.length - 2}</span>` 
      : (loot.length === 0 ? `<span class="badge-pill" style="opacity: 0.6;">None</span>` : "");

    const locationText = (m.Location && m.Location.length > 0)
      ? m.Location.join(", ")
      : "Unknown or Unspecified";

    return `
      <article class="monster-card" data-name="${escapeHtml(m.Name)}" id="card-${sanitizeId(m.Name)}">
        <div class="card-top">
          <span class="card-class-badge">${escapeHtml(m.Class || "Unknown")}</span>
          <h2 class="card-title">${escapeHtml(m.Name)}</h2>
          <p class="card-location" title="${escapeHtml(locationText)}">📍 ${escapeHtml(locationText)}</p>
        </div>

        <div class="card-middle">
          <div class="card-section">
            <span class="card-section-label">Vulnerabilities</span>
            <div class="card-pills-row">
              ${weaknessBadges || `<span class="badge-pill" style="opacity:0.5;">None recorded</span>`}
              ${moreWeakness}
            </div>
          </div>

          <div class="card-section">
            <span class="card-section-label">Alchemical Remains & Loot</span>
            <div class="card-pills-row">
              ${lootBadges}
              ${moreLoot}
            </div>
          </div>
        </div>

        <div class="card-footer-action">
          <span class="inspect-text">Open Dossier</span>
          <span class="arrow-icon">→</span>
        </div>
      </article>
    `;
  }

  function getWeaknessBadgeClass(w) {
    const wl = w.toLowerCase();
    if (wl.includes("igni")) return "weakness-igni";
    if (wl.includes("quen")) return "weakness-quen";
    if (wl.includes("aard")) return "weakness-aard";
    if (wl.includes("axii")) return "weakness-axii";
    if (wl.includes("yrden")) return "weakness-yrden";
    if (wl.includes("oil")) return "weakness-oil";
    if (["bomb", "wind", "dust", "puffball", "dimeritium"].some(b => wl.includes(b))) return "weakness-bomb";
    return "";
  }

  function findRecipeForIngredient(ingredientName) {
    if (!ingredientName) return null;
    const ingrLower = ingredientName.toLowerCase();
    return allRecipes.find(r => 
      (r.monster_ingredient && r.monster_ingredient.toLowerCase() === ingrLower) ||
      (r.monster_ingredient && ingrLower.includes(r.monster_ingredient.toLowerCase())) ||
      (r.all_ingredients && r.all_ingredients.some(i => i.toLowerCase() === ingrLower))
    );
  }

  // -------------------------------------------------------------
  // 3. Tooltips (Tippy.js Integration)
  // -------------------------------------------------------------
  function initSignTooltips() {
    if (typeof tippy === "undefined") return;

    document.querySelectorAll(".sign-pill").forEach(pill => {
      const sign = pill.dataset.sign;
      if (SIGN_TOOLTIPS[sign]) {
        tippy(pill, {
          content: SIGN_TOOLTIPS[sign],
          allowHTML: true,
          theme: "witcher",
          placement: "bottom",
          animation: "fade"
        });
      }
    });
  }

  function initCardTooltips() {
    if (typeof tippy === "undefined") return;

    // Attach alchemy tooltips to loot badges that have matching recipes
    document.querySelectorAll(".badge-pill.has-recipe").forEach(pill => {
      const ingr = pill.dataset.ingredient;
      const recipe = findRecipeForIngredient(ingr);
      if (recipe) {
        tippy(pill, {
          content: `<strong>⚗️ Used in: ${escapeHtml(recipe.name)}</strong><br><em>${escapeHtml(recipe.effect)}</em><br><span style="color:#d4af37; font-size:0.75rem;">Click to open Alchemy Lab</span>`,
          allowHTML: true,
          theme: "witcher",
          placement: "top",
          interactive: true
        });

        pill.addEventListener("click", (e) => {
          e.stopPropagation();
          openAlchemyLabWithSearch(recipe.name);
        });
      }
    });
  }

  // -------------------------------------------------------------
  // 4. Filtering & Fuzzy Search Logic (Fuse.js)
  // -------------------------------------------------------------
  function applyFilters() {
    let pool = allMonsters;

    // 1. Fuzzy Search with Fuse.js (if query provided)
    if (searchQuery.trim() !== "") {
      if (monsterFuse) {
        const results = monsterFuse.search(searchQuery.trim());
        pool = results.map(res => res.item);
      } else {
        const q = searchQuery.toLowerCase();
        pool = pool.filter(m => 
          (m.Name || "").toLowerCase().includes(q) ||
          (m.Class || "").toLowerCase().includes(q) ||
          (m.Weaknesses || []).some(w => w.toLowerCase().includes(q)) ||
          (m.Loot || []).some(item => item.toLowerCase().includes(q))
        );
      }
    }

    // 2. Class filter
    if (activeClass !== "all") {
      pool = pool.filter(m => (m.Class || "").toLowerCase().includes(activeClass.toLowerCase()));
    }

    // 3. Sign filter
    if (activeSign) {
      const signLower = activeSign.toLowerCase();
      pool = pool.filter(m => (m.Weaknesses || []).some(w => w.toLowerCase().includes(signLower)));
    }

    filteredMonsters = pool;
    renderMonsters();
  }

  function updateResetButtonVisibility() {
    const isFiltered = activeClass !== "all" || activeSign !== null || searchQuery !== "";
    resetFiltersBtn.style.display = isFiltered ? "inline-block" : "none";
    clearSearchBtn.style.display = searchQuery ? "inline-block" : "none";
  }

  function resetAllFilters() {
    activeClass = "all";
    activeSign = null;
    searchQuery = "";
    searchInput.value = "";

    document.querySelectorAll(".class-pill").forEach(p => {
      p.classList.toggle("active", p.dataset.class === "all");
    });

    document.querySelectorAll(".sign-pill").forEach(p => {
      p.classList.remove("active");
    });

    applyFilters();
  }

  // -------------------------------------------------------------
  // 5. Alchemy Lab Functionality
  // -------------------------------------------------------------
  function renderAlchemyRecipes() {
    if (!alchemyRecipesGrid) return;

    if (filteredRecipes.length === 0) {
      alchemyRecipesGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <p>No alchemy formula matches your criteria.</p>
        </div>
      `;
      if (alchemyResultsInfo) alchemyResultsInfo.textContent = "Showing 0 recipes";
      return;
    }

    if (alchemyResultsInfo) {
      alchemyResultsInfo.textContent = `Showing ${filteredRecipes.length} of ${allRecipes.length} recipes`;
    }

    alchemyRecipesGrid.innerHTML = filteredRecipes.map(r => {
      const typeClass = r.type === "Decoction" ? "type-decoction" : r.type === "Blade Oil" ? "type-oil" : "type-potion";
      const icon = r.type === "Decoction" ? "🧪" : r.type === "Blade Oil" ? "🗡️" : "⚗️";

      const targets = (r.target_monsters || []).map(mName => {
        return `<button class="target-beast-btn" data-monster="${escapeHtml(mName)}">Hunt ${escapeHtml(mName)}</button>`;
      }).join("");

      return `
        <div class="recipe-card">
          <div>
            <div class="recipe-header">
              <span class="recipe-title">${icon} ${escapeHtml(r.name)}</span>
              <span class="recipe-type-badge ${typeClass}">${escapeHtml(r.type)}</span>
            </div>

            <div class="recipe-toxicity">
              <span>☠️ Toxicity: ${r.toxicity || 0}</span>
            </div>

            <div class="recipe-effect">
              "${escapeHtml(r.effect)}"
            </div>
          </div>

          <div class="recipe-ingredient-box">
            <span class="ingredient-label">Required Monster Component</span>
            <span class="ingredient-name">💎 ${escapeHtml(r.monster_ingredient || "Monster Remnant")}</span>
            ${targets ? `<div class="recipe-targets-row">${targets}</div>` : ""}
          </div>
        </div>
      `;
    }).join("");

    // Attach hunt button events
    alchemyRecipesGrid.querySelectorAll(".target-beast-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const monsterName = btn.dataset.monster;
        closeAlchemyLab();
        searchMonsterDirectly(monsterName);
      });
    });
  }

  function applyAlchemyFilters() {
    let pool = allRecipes;

    // Fuzzy search with Fuse.js
    if (alchemySearchQuery.trim() !== "") {
      if (alchemyFuse) {
        const results = alchemyFuse.search(alchemySearchQuery.trim());
        pool = results.map(res => res.item);
      } else {
        const q = alchemySearchQuery.toLowerCase();
        pool = pool.filter(r => 
          (r.name || "").toLowerCase().includes(q) ||
          (r.effect || "").toLowerCase().includes(q) ||
          (r.monster_ingredient || "").toLowerCase().includes(q)
        );
      }
    }

    // Type filter
    if (activeAlchemyType !== "all") {
      pool = pool.filter(r => r.type === activeAlchemyType);
    }

    filteredRecipes = pool;
    renderAlchemyRecipes();
  }

  function openAlchemyLab() {
    alchemyModal.classList.add("open");
    alchemyModal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeAlchemyLab() {
    alchemyModal.classList.remove("open");
    alchemyModal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function openAlchemyLabWithSearch(query) {
    openAlchemyLab();
    if (alchemySearchInput) {
      alchemySearchInput.value = query;
      alchemySearchQuery = query;
      applyAlchemyFilters();
    }
  }

  function searchMonsterDirectly(monsterName) {
    searchInput.value = monsterName;
    searchQuery = monsterName;
    applyFilters();

    // If exact match found, open its dossier directly!
    const exactMonster = allMonsters.find(m => m.Name.toLowerCase() === monsterName.toLowerCase());
    if (exactMonster) {
      setTimeout(() => openDossier(exactMonster), 200);
    }
  }

  // -------------------------------------------------------------
  // 6. Dossier Modal & Combat Prep
  // -------------------------------------------------------------
  function openDossier(m) {
    document.getElementById("modal-monster-name").textContent = m.Name;
    document.getElementById("modal-class-badge").textContent = m.Class || "Unknown";
    
    const locs = m.Location && m.Location.length > 0 ? m.Location.join(", ") : "Habitat uncharted";
    document.getElementById("modal-locations").textContent = `Confirmed Habitats: ${locs}`;

    // Combat Tactics Calculation
    const isBeast = (m.Class || "").toLowerCase().includes("beast");
    document.getElementById("modal-sword-type").innerHTML = isBeast
      ? `<span style="color: #cbd5e1;">⚔️ Steel Sword</span> (Beasts & Animals)`
      : `<span style="color: #38bdf8;">✨ Silver Sword</span> (Monsters & Hybrids)`;

    // Detect blade oil
    const oils = (m.Weaknesses || []).filter(w => w.toLowerCase().includes("oil"));
    document.getElementById("modal-tactics-oil").textContent = oils.length > 0 ? oils.join(", ") : "Standard Blade Oil";

    // Detect signs
    const signs = (m.Weaknesses || []).filter(w => ["igni", "quen", "aard", "axii", "yrden"].some(s => w.toLowerCase().includes(s)));
    document.getElementById("modal-tactics-sign").textContent = signs.length > 0 ? signs.join(", ") : "Any Witcher Sign";

    // Detect bombs
    const bombs = (m.Weaknesses || []).filter(w => ["bomb", "wind", "dust", "puffball", "dimeritium"].some(b => w.toLowerCase().includes(b)));
    document.getElementById("modal-tactics-bomb").textContent = bombs.length > 0 ? bombs.join(", ") : "Grapeshot / Moon Dust";

    // Weaknesses tags
    const weakContainer = document.getElementById("modal-weaknesses-tags");
    if (m.Weaknesses && m.Weaknesses.length > 0) {
      weakContainer.innerHTML = m.Weaknesses.map(w => {
        const pillClass = getWeaknessBadgeClass(w);
        return `<span class="badge-pill ${pillClass}" style="font-size:0.86rem; padding: 0.35rem 0.8rem;">${escapeHtml(w)}</span>`;
      }).join("");
    } else {
      weakContainer.innerHTML = `<span style="color: var(--text-muted);">None known</span>`;
    }

    // Loot drops tags with recipe detection
    const lootContainer = document.getElementById("modal-loot-tags");
    if (m.Loot && m.Loot.length > 0) {
      lootContainer.innerHTML = m.Loot.map(item => {
        const recipe = findRecipeForIngredient(item);
        const recipeClass = recipe ? "has-recipe" : "";
        const icon = recipe ? "⚗️ " : "";
        return `<span class="badge-pill loot-pill ${recipeClass}" style="font-size:0.86rem; padding: 0.35rem 0.8rem;" data-ingredient="${escapeHtml(item)}">${icon}${escapeHtml(item)}</span>`;
      }).join("");
    } else {
      lootContainer.innerHTML = `<span style="color: var(--text-muted);">None recorded</span>`;
    }

    dossierModal.classList.add("open");
    dossierModal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";

    // Attach tooltips inside dossier
    initCardTooltips();
  }

  function closeDossier() {
    dossierModal.classList.remove("open");
    dossierModal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function openPrepModal() {
    combatPrepModal.classList.add("open");
    combatPrepModal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closePrepModal() {
    combatPrepModal.classList.remove("open");
    combatPrepModal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function handlePrepSelectChange() {
    const selectedName = prepMonsterSelect.value;
    if (!selectedName) {
      prepResultDisplay.style.display = "none";
      return;
    }

    const m = allMonsters.find(monster => monster.Name === selectedName);
    if (!m) return;

    const isBeast = (m.Class || "").toLowerCase().includes("beast");
    const oils = (m.Weaknesses || []).filter(w => w.toLowerCase().includes("oil"));
    const signs = (m.Weaknesses || []).filter(w => ["igni", "quen", "aard", "axii", "yrden"].some(s => w.toLowerCase().includes(s)));
    const bombs = (m.Weaknesses || []).filter(w => ["bomb", "wind", "dust", "puffball", "dimeritium"].some(b => w.toLowerCase().includes(b)));

    prepResultDisplay.innerHTML = `
      <div class="tactics-box" style="margin-top: 1rem;">
        <div class="tactics-title">Tactical Briefing: ${escapeHtml(m.Name)} (${escapeHtml(m.Class || "Unknown")})</div>
        <div class="tactics-grid">
          <div class="tactic-item">
            <span class="tactic-label">Primary Blade</span>
            <span class="tactic-val">${isBeast ? "⚔️ Steel Blade" : "✨ Silver Blade"}</span>
          </div>
          <div class="tactic-item">
            <span class="tactic-label">Blade Oil</span>
            <span class="tactic-val" style="color: var(--sign-oil);">${oils.length ? oils.join(", ") : "Standard Oil"}</span>
          </div>
          <div class="tactic-item">
            <span class="tactic-label">Sign Tactics</span>
            <span class="tactic-val" style="color: var(--sign-igni);">${signs.length ? signs.join(", ") : "Igni / Quen"}</span>
          </div>
          <div class="tactic-item">
            <span class="tactic-label">Bombs / Elixirs</span>
            <span class="tactic-val" style="color: var(--sign-bomb);">${bombs.length ? bombs.join(", ") : "Grapeshot"}</span>
          </div>
        </div>
      </div>
    `;
    prepResultDisplay.style.display = "block";
  }

  // -------------------------------------------------------------
  // 7. Event Listeners Setup
  // -------------------------------------------------------------
  function setupEventListeners() {
    // Bestiary Search Input
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        searchQuery = e.target.value;
        applyFilters();
      }, 100);
    });

    clearSearchBtn.addEventListener("click", () => {
      searchInput.value = "";
      searchQuery = "";
      applyFilters();
    });

    // Class Category Pills
    document.querySelectorAll(".class-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        // If inside alchemy modal, ignore here
        if (pill.closest("#alchemy-modal")) return;
        document.querySelectorAll(".class-pills .class-pill").forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        activeClass = pill.dataset.class;
        applyFilters();
      });
    });

    // Sign Vulnerability Pills
    document.querySelectorAll(".sign-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const sign = pill.dataset.sign;
        if (activeSign === sign) {
          pill.classList.remove("active");
          activeSign = null;
        } else {
          document.querySelectorAll(".sign-pill").forEach(p => p.classList.remove("active"));
          pill.classList.add("active");
          activeSign = sign;
        }
        applyFilters();
      });
    });

    // Reset All Filters
    resetFiltersBtn.addEventListener("click", resetAllFilters);

    // Random Encounter Button
    randomBtn.addEventListener("click", () => {
      if (allMonsters.length === 0) return;
      const randomMonster = allMonsters[Math.floor(Math.random() * allMonsters.length)];
      openDossier(randomMonster);
    });

    // Combat Prep Calculator Modal
    prepModeBtn.addEventListener("click", openPrepModal);
    prepMonsterSelect.addEventListener("change", handlePrepSelectChange);
    prepModalCloseBtn.addEventListener("click", closePrepModal);
    combatPrepModal.addEventListener("click", (e) => {
      if (e.target === combatPrepModal) closePrepModal();
    });

    // Alchemy Lab Modal
    alchemyBtn.addEventListener("click", openAlchemyLab);
    alchemyModalCloseBtn.addEventListener("click", closeAlchemyLab);
    alchemyModal.addEventListener("click", (e) => {
      if (e.target === alchemyModal) closeAlchemyLab();
    });

    // Alchemy Search Input
    let alchemyDebounce;
    alchemySearchInput.addEventListener("input", (e) => {
      clearTimeout(alchemyDebounce);
      alchemyDebounce = setTimeout(() => {
        alchemySearchQuery = e.target.value;
        applyAlchemyFilters();
      }, 100);
    });

    // Alchemy Type Pills
    document.querySelectorAll("#alchemy-type-filters .class-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        document.querySelectorAll("#alchemy-type-filters .class-pill").forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        activeAlchemyType = pill.dataset.type;
        applyAlchemyFilters();
      });
    });

    // Dossier Modal Close
    modalCloseBtn.addEventListener("click", closeDossier);
    dossierModal.addEventListener("click", (e) => {
      if (e.target === dossierModal) closeDossier();
    });

    // Global Escape Key to close any active modal
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeDossier();
        closePrepModal();
        closeAlchemyLab();
      }
    });
  }

  // Utilities
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function sanitizeId(str) {
    return (str || "").toLowerCase().replace(/[^a-z0-9]/g, "-");
  }

  // Launch the App
  init();
});
