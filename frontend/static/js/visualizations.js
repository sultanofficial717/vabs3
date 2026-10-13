/**
 * Autism Lens - Visualization Engine
 * Renders normative Vineland-3 standard score charts, subdomain maps,
 * strengths & weaknesses comparisons, and DSM-5-TR ASD pattern badges.
 */
const Visualizations = {
  renderResults(containerId, resultsData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const scores = resultsData.scores || {};
    const domains = scores.domains || {};
    const composite = scores.composite || {};
    const subdomains = scores.subdomains || {};
    const patterns = resultsData.patterns || {};
    const sw = scores.strength_weakness || [];

    let html = `
      <!-- ABC Composite & Summary Metrics -->
      <div class="kpi-grid" style="margin-bottom: 1.5rem;">
        <div class="kpi-card" style="border-top: 3px solid var(--accent-yellow);">
          <div class="kpi-title">Adaptive Behavior Composite (ABC)</div>
          <div class="kpi-val">${composite.abc !== null && composite.abc !== undefined ? composite.abc : "—"}</div>
          <div class="kpi-footer">
            <span class="badge ${this.getBandBadgeClass(composite.abc_band)}">${composite.abc_band || "Incomplete"}</span>
            <span style="margin-left: auto;">%ile: <strong>${composite.percentile || "—"}</strong></span>
          </div>
          <div style="font-size: 0.725rem; color: var(--text-secondary); margin-top: 0.35rem;">
            90% CI: ${composite.ci && composite.ci["90"] ? composite.ci["90"].text : "—"}
          </div>
        </div>

        <div class="kpi-card" style="border-top: 3px solid ${this.getLikelihoodBorderColor(patterns.asd_profile_likelihood)};">
          <div class="kpi-title">ASD Profile Likelihood</div>
          <div style="font-size: 1.1rem; font-weight: 800; margin: 0.35rem 0; color: var(--text-main); line-height: 1.3;">
            ${patterns.asd_profile_likelihood ? patterns.asd_profile_likelihood.label : "Analyzed"}
          </div>
          <div class="kpi-footer">
            <span class="badge ${this.getLikelihoodBadge(patterns.asd_profile_likelihood)}">
              DSM-5-TR Grounded
            </span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-title">Personal Mean SS</div>
          <div class="kpi-val">${scores.mean_ss || 100}</div>
          <div class="kpi-footer">Intra-individual baseline</div>
        </div>

        <div class="kpi-card">
          <div class="kpi-title">Subdomain Scatter Range</div>
          <div class="kpi-val">${patterns.score_range || 0} <span style="font-size: 1rem; font-weight: normal; color: var(--text-secondary);">pts</span></div>
          <div class="kpi-footer">Range across domains</div>
        </div>
      </div>

      <!-- Domain Standard Scores Bar Visualization -->
      <div class="card" style="margin-bottom: 1.5rem;">
        <div class="card-header-flex">
          <div>
            <h4 class="card-title">Domain Standard Scores (Mean = 100, SD = 15)</h4>
            <p class="card-subtitle">Normal adequate range is 80–114. Scores below 70 indicate developmental deficits.</p>
          </div>
          <div style="font-size: 0.75rem; color: var(--text-secondary);">
            <span style="display: inline-block; width: 10px; height: 10px; background-color: #475569; margin-right: 4px; vertical-align: middle;"></span>
            Population Mean (100)
          </div>
        </div>
        ${this.renderDomainBars(domains)}
      </div>

      <!-- Strengths and Weaknesses -->
      ${this.renderStrengthsWeaknesses(sw, scores.mean_ss)}

      <!-- Subdomain v-Scale Profiles Table -->
      <div class="card" style="margin-bottom: 1.5rem;">
        <h4 class="card-title" style="margin-bottom: 0.25rem;">Subdomain v-Scale Breakdown (Mean = 15, SD = 3)</h4>
        <p class="card-subtitle" style="margin-bottom: 1rem;">Detailed item mastery, age equivalents, and growth scale values.</p>
        <div class="data-table-wrapper">
          <table class="table-clean">
            <thead>
              <tr>
                <th>Subdomain</th>
                <th>Domain</th>
                <th>Raw Score</th>
                <th>v-Scale Score</th>
                <th>Classification</th>
                <th>Age Equivalent</th>
                <th>Growth Scale (GSV)</th>
              </tr>
            </thead>
            <tbody>
              ${this.renderSubdomainRows(subdomains)}
            </tbody>
          </table>
        </div>
      </div>

      <!-- DSM-5-TR Grounded ASD Pattern Cards -->
      <div class="card">
        <h4 class="card-title" style="margin-bottom: 0.25rem;">ASD Pattern Engine Recognitions (DSM-5-TR Rules)</h4>
        <p class="card-subtitle" style="margin-bottom: 1rem;">Evidence-grounded pattern identification based on domain ordering and scatter.</p>
        ${this.renderPatternCards(patterns)}
      </div>
    `;

    container.innerHTML = html;
  },

  renderDomainBars(domains) {
    const list = [
      { code: "COM", name: "Communication" },
      { code: "DLS", name: "Daily Living Skills" },
      { code: "SOC", name: "Socialization" },
      { code: "MOT", name: "Motor Skills" },
    ];

    return list.map(item => {
      const d = domains[item.code] || {};
      const ss = d.ss !== null && d.ss !== undefined ? d.ss : 0;
      // Map score 20..160 to percentage 0..100%
      const pct = Math.max(0, Math.min(100, ((ss - 20) / 140) * 100));
      const ciText = d.ci && d.ci["90"] ? d.ci["90"].text : "—";
      const color = this.getScoreColor(ss);

      return `
        <div class="score-bar-row">
          <div class="score-bar-meta">
            <span><strong>${item.name} (${item.code})</strong></span>
            <span>
              Standard Score: <strong>${ss}</strong>
              <span class="badge ${this.getBandBadgeClass(d.band)}" style="margin-left: 0.35rem;">${d.band || "—"}</span>
              <span style="color: var(--text-secondary); margin-left: 0.5rem;">90% CI: ${ciText} | %ile: ${d.percentile || "—"}</span>
            </span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width: ${pct}%; background-color: ${color};">
              ${ss >= 30 ? ss : ""}
            </div>
            <!-- Population Mean Reference (100) -> ((100-20)/140)*100 = 57.1% -->
            <div class="norm-mean-divider" title="Population Mean = 100"></div>
          </div>
        </div>
      `;
    }).join("");
  },

  renderStrengthsWeaknesses(swList, meanSS) {
    if (!swList || swList.length === 0) return "";

    return `
      <div class="card" style="margin-bottom: 1.5rem;">
        <h4 class="card-title" style="margin-bottom: 0.25rem;">Intra-Individual Strengths & Weaknesses</h4>
        <p class="card-subtitle" style="margin-bottom: 1rem;">Evaluated against patient's personal mean standard score (${meanSS}). Difference >= +10 indicates relative strength; <= -10 indicates relative weakness.</p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
          ${swList.map(s => {
            const isStrength = s.verdict === "Strength";
            const isWeak = s.verdict === "Weakness";
            const badgeClass = isStrength ? "badge-completed" : (isWeak ? "badge-danger" : "badge-neutral");
            const borderCol = isStrength ? "var(--success)" : (isWeak ? "var(--error)" : "var(--border-color)");
            return `
              <div style="border-left: 4px solid ${borderCol}; background-color: #FFFFFF; border-top: 1px solid var(--border-color); border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); padding: 1rem; border-radius: var(--radius-md);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                  <strong style="font-size: 0.9rem;">${s.name} (${s.domain})</strong>
                  <span class="badge ${badgeClass}">${s.verdict}</span>
                </div>
                <div style="font-size: 0.825rem; color: var(--text-main); margin-bottom: 0.2rem;">
                  Difference: <strong>${s.diff > 0 ? "+" + s.diff : s.diff} pts</strong> (Score: ${s.ss})
                </div>
                <div style="font-size: 0.725rem; color: var(--text-secondary);">
                  Population base rate: ${s.base_rate}
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  },

  renderSubdomainRows(subs) {
    const codes = ["rec", "exp", "wrn", "per", "dom", "cmm", "ipr", "pla", "cop", "gmo", "fmo"];
    return codes.map(c => {
      const s = subs[c] || {};
      const v = s.v !== null && s.v !== undefined ? s.v : "—";
      const badgeClass = v <= 9 ? "badge-danger" : (v <= 12 ? "badge-review" : "badge-completed");
      return `
        <tr>
          <td><strong>${s.name || c}</strong></td>
          <td>${s.domain || "—"}</td>
          <td>${s.raw !== null ? s.raw : "—"}</td>
          <td><strong>${v}</strong></td>
          <td><span class="badge ${badgeClass}">${s.band || "—"}</span></td>
          <td>${s.age_equiv || "—"}</td>
          <td>${s.gsv || "—"}</td>
        </tr>
      `;
    }).join("");
  },

  renderPatternCards(patterns) {
    const list = patterns.patterns || [];
    const flags = patterns.flags || [];

    if (list.length === 0 && flags.length === 0) {
      return `<p style="font-size: 0.85rem; color: var(--text-secondary);">No significant atypical ASD-specific scatter identified on current score profile.</p>`;
    }

    let cardsHtml = list.map(p => {
      const severityClass = p.severity === "high" ? "badge-danger" : "badge-review";
      const borderCol = p.severity === "high" ? "var(--error)" : "var(--warning)";
      return `
        <div style="border-left: 4px solid ${borderCol}; background-color: #FFFFFF; border-top: 1px solid var(--border-color); border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); padding: 1rem 1.25rem; border-radius: var(--radius-md); margin-bottom: 0.75rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <strong style="font-size: 0.95rem; color: var(--text-main);">${p.name}</strong>
            <span class="badge ${severityClass}">${p.severity.toUpperCase()}</span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-main); margin-bottom: 0.4rem; line-height: 1.45;">${p.description}</p>
          <div style="font-size: 0.75rem; color: var(--text-secondary); font-style: italic;">Clinical Basis: ${p.dsm_link}</div>
        </div>
      `;
    }).join("");

    if (flags.length > 0) {
      cardsHtml += `
        <h5 style="margin: 1.25rem 0 0.5rem; font-size: 0.85rem; color: var(--error);">Critical Item Indicators (DSM-5-TR Criterion Behaviors):</h5>
        ${flags.map(f => `
          <div style="background-color: var(--error-bg); border-left: 3px solid var(--error); padding: 0.65rem 0.85rem; border-radius: 4px; font-size: 0.8rem; margin-bottom: 0.5rem; color: var(--error-text);">
            ${f.text}
          </div>
        `).join("")}
      `;
    }

    return cardsHtml;
  },

  getScoreColor(ss) {
    if (ss < 70) return "#EF4444"; // Low / Red
    if (ss < 80) return "#F59E0B"; // Moderately Low / Amber
    if (ss <= 114) return "#10B981"; // Adequate / Green
    return "#3B82F6"; // High / Blue
  },

  getBandBadgeClass(band) {
    if (!band) return "badge-neutral";
    if (band === "Low") return "badge-danger";
    if (band === "Moderately Low") return "badge-review";
    if (band === "Adequate") return "badge-completed";
    return "badge-yellow";
  },

  getLikelihoodBorderColor(like) {
    if (!like) return "var(--border-color)";
    if (like.color === "danger") return "var(--error)";
    if (like.color === "warning") return "var(--warning)";
    return "var(--info)";
  },

  getLikelihoodBadge(like) {
    if (!like) return "badge-neutral";
    if (like.color === "danger") return "badge-danger";
    if (like.color === "warning") return "badge-review";
    return "badge-completed";
  },
};

window.Visualizations = Visualizations;
