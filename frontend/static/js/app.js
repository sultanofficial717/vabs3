/**
 * Autism Lens — Application Shell, Router & Global UI Controller
 * Includes Toast Notifications, Confirmation Modal, Persistent Settings,
 * Sidebar Management, and View Routers.
 */

// ============================================================================
// TOAST NOTIFICATION UTILITY
// ============================================================================
const Toast = {
  show(message, type = "info", duration = 3500) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-item toast-${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✓";
    else if (type === "error") icon = "✕";
    else if (type === "warning") icon = "⚠️";

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <div class="toast-content">${message}</div>
      <button class="toast-close" type="button" aria-label="Dismiss">&times;</button>
    `;

    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(8px)";
        setTimeout(() => toast.remove(), 200);
      });
    }

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(8px)";
        setTimeout(() => toast.remove(), 250);
      }
    }, duration);
  },
};
window.Toast = Toast;

// ============================================================================
// MODAL DIALOG UTILITY
// ============================================================================
const Modal = {
  onConfirmCallback: null,

  confirm({ title = "Confirm Action", message = "Are you sure?", confirmText = "Confirm", cancelText = "Cancel", onConfirm = null }) {
    const modal = document.getElementById("confirm-modal");
    const titleEl = document.getElementById("modal-title");
    const bodyEl = document.getElementById("modal-body");
    const confirmBtn = document.getElementById("modal-confirm-btn");
    const cancelBtn = document.getElementById("modal-cancel-btn");

    if (!modal) return;

    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.textContent = message;
    if (confirmBtn) confirmBtn.textContent = confirmText;
    if (cancelBtn) cancelBtn.textContent = cancelText;

    this.onConfirmCallback = onConfirm;

    if (confirmBtn) {
      confirmBtn.onclick = () => {
        Modal.close();
        if (typeof Modal.onConfirmCallback === "function") {
          Modal.onConfirmCallback();
        }
      };
    }

    modal.style.display = "flex";
  },

  close() {
    const modal = document.getElementById("confirm-modal");
    if (modal) modal.style.display = "none";
    this.onConfirmCallback = null;
  },
};
window.Modal = Modal;

// ============================================================================
// APP CONTROLLER
// ============================================================================
const App = {
  currentView: "overview",
  assessmentsCache: [],
  patientsCache: [],
  reportsCache: [],
  analyticsCache: null,

  init() {
    this.bindNavigation();
    this.bindSidebarToggles();
    this.bindGlobalSearch();
    this.bindFilters();
    this.loadSettings();

    // Initialize 8-step wizard
    if (window.Wizard && typeof Wizard.init === "function") {
      Wizard.init();
    }

    // Check system health
    this.checkSystemHealth();

    // Load workspace data
    this.refreshData();

    // Handle Escape key globally for modals and drawer
    window.addEventListener("keydown", e => {
      if (e.key === "Escape") {
        Modal.close();
        this.closeMobileSidebar();
      }
    });
  },

  bindNavigation() {
    document.querySelectorAll(".nav-item-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const view = btn.dataset.view;
        if (view) {
          this.navigateTo(view);
        }
      });
    });
  },

  bindSidebarToggles() {
    const sidebar = document.getElementById("app-sidebar");
    const mainWrapper = document.querySelector(".main-wrapper");
    const toggleBtn = document.getElementById("sidebar-toggle-btn");
    const mobileBtn = document.getElementById("mobile-menu-btn");
    const backdrop = document.getElementById("app-backdrop");

    // Restore desktop collapsed state from localStorage
    const savedCollapsed = localStorage.getItem("autism_lens_sidebar_collapsed") === "true";
    if (savedCollapsed && sidebar && mainWrapper) {
      sidebar.classList.add("collapsed");
      mainWrapper.classList.add("sidebar-collapsed");
      if (toggleBtn) toggleBtn.textContent = "▸";
    }

    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", () => {
        const isCollapsed = sidebar.classList.toggle("collapsed");
        if (mainWrapper) mainWrapper.classList.toggle("sidebar-collapsed", isCollapsed);
        toggleBtn.textContent = isCollapsed ? "▸" : "◂";
        localStorage.setItem("autism_lens_sidebar_collapsed", isCollapsed ? "true" : "false");
      });
    }

    if (mobileBtn && sidebar) {
      mobileBtn.addEventListener("click", () => {
        this.toggleMobileSidebar();
      });
    }

    if (backdrop) {
      backdrop.addEventListener("click", () => {
        this.closeMobileSidebar();
      });
    }
  },

  toggleMobileSidebar() {
    const sidebar = document.getElementById("app-sidebar");
    const backdrop = document.getElementById("app-backdrop");
    if (!sidebar) return;

    const isOpen = sidebar.classList.toggle("mobile-open");
    if (backdrop) backdrop.classList.toggle("visible", isOpen);
  },

  closeMobileSidebar() {
    const sidebar = document.getElementById("app-sidebar");
    const backdrop = document.getElementById("app-backdrop");
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (backdrop) backdrop.classList.remove("visible");
  },

  bindGlobalSearch() {
    const input = document.getElementById("global-search-input");
    if (!input) return;

    // Keyboard shortcut ⌘K or Ctrl+K
    window.addEventListener("keydown", e => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        input.focus();
        input.select();
      }
    });

    let debounceTimer = null;
    input.addEventListener("input", e => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const q = e.target.value.trim().toLowerCase();
        if (q.length > 0) {
          this.navigateTo("history");
          const histInput = document.getElementById("history-search-input");
          if (histInput) {
            histInput.value = q;
            this.loadHistory(q);
          }
        }
      }, 200);
    });
  },

  bindFilters() {
    // Overview filter
    const ovFilter = document.getElementById("overview-status-filter");
    if (ovFilter) {
      ovFilter.addEventListener("change", e => {
        this.loadRecentAssessments(e.target.value);
      });
    }

    // History filters with debouncing
    const histSearch = document.getElementById("history-search-input");
    const histStatus = document.getElementById("history-status-filter");
    let histDebounce = null;

    if (histSearch) {
      histSearch.addEventListener("input", e => {
        clearTimeout(histDebounce);
        histDebounce = setTimeout(() => {
          this.loadHistory(e.target.value, histStatus ? histStatus.value : "all");
        }, 150);
      });
    }

    if (histStatus) {
      histStatus.addEventListener("change", e => {
        this.loadHistory(histSearch ? histSearch.value : "", e.target.value);
      });
    }

    // Patients filter
    const patSearch = document.getElementById("patients-search-input");
    let patDebounce = null;
    if (patSearch) {
      patSearch.addEventListener("input", e => {
        clearTimeout(patDebounce);
        patDebounce = setTimeout(() => {
          this.loadPatients(e.target.value);
        }, 150);
      });
    }
  },

  navigateTo(viewName) {
    this.currentView = viewName;

    // Update Sidebar Navigation state
    document.querySelectorAll(".nav-item-btn").forEach(btn => {
      btn.classList.remove("active");
      if (btn.dataset.view === viewName) {
        btn.classList.add("active");
      }
    });

    // Update Breadcrumb
    const crumbTitle = document.getElementById("crumb-current-title");
    if (crumbTitle) {
      crumbTitle.textContent = this.formatViewTitle(viewName);
    }

    // Hide all view panels and show target
    document.querySelectorAll(".view-panel").forEach(panel => {
      panel.classList.remove("active");
      panel.style.display = "none";
    });

    const activePanel = document.getElementById(`view-${viewName}`);
    if (activePanel) {
      activePanel.classList.add("active");
      activePanel.style.display = "block";
    }

    // Dismiss mobile drawer
    this.closeMobileSidebar();

    // View-specific data reloads
    if (viewName === "overview") this.refreshOverview();
    if (viewName === "history") this.loadHistory();
    if (viewName === "patients") this.loadPatients();
    if (viewName === "reports") this.loadReports();
    if (viewName === "analytics") this.loadAnalytics();

    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  formatViewTitle(view) {
    switch (view) {
      case "overview": return "Overview Dashboard";
      case "new-assessment": return "New Assessment Wizard";
      case "history": return "Assessments History";
      case "patients": return "Patients Directory";
      case "reports": return "Clinical Reports Library";
      case "analytics": return "Clinical Analytics & Metrics";
      case "settings": return "System Settings";
      case "help": return "Norms & Clinical Documentation";
      default: return "Dashboard";
    }
  },

  async checkSystemHealth() {
    try {
      const health = await API.checkHealth();
      const statusText = document.getElementById("top-system-status");
      if (health.status === "healthy") {
        if (statusText) statusText.textContent = "Pearson VABS-3 Active • API Connected";
      } else {
        if (statusText) statusText.textContent = "Backend Offline";
      }
    } catch (e) {
      const statusText = document.getElementById("top-system-status");
      if (statusText) statusText.textContent = "Backend Offline";
    }
  },

  async refreshData() {
    await Promise.all([
      this.refreshOverview(),
      this.loadHistory(),
      this.loadPatients(),
      this.loadReports(),
      this.loadAnalytics(),
    ]);
  },

  async refreshOverview() {
    try {
      // 1. Load Analytics KPIs
      const analyticsRes = await API.fetchAnalytics();
      if (analyticsRes.ok && analyticsRes.analytics) {
        this.analyticsCache = analyticsRes.analytics;
        const a = analyticsRes.analytics;
        const setEl = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val !== null && val !== undefined ? val : "—";
        };
        setEl("kpi-total-assessments", a.total_assessments || 0);
        setEl("kpi-completed-assessments", a.completed_assessments || 0);
        setEl("kpi-reports-count", a.reports_generated || 0);
        setEl("kpi-awaiting-review", a.awaiting_review || 0);

        this.renderDomainBenchmarks(a.average_domain_scores || {});
      }

      // 2. Load Recent Assessments
      const statusFilter = document.getElementById("overview-status-filter")?.value || "all";
      await this.loadRecentAssessments(statusFilter);

    } catch (err) {
      console.warn("Could not load overview analytics:", err);
    }
  },

  renderDomainBenchmarks(avgScores) {
    const container = document.getElementById("overview-domain-benchmarks");
    if (!container) return;

    const domains = [
      { code: "COM", name: "Communication", score: avgScores.COM || 75 },
      { code: "DLS", name: "Daily Living Skills", score: avgScores.DLS || 81 },
      { code: "SOC", name: "Socialization", score: avgScores.SOC || 66 },
      { code: "MOT", name: "Motor Skills", score: avgScores.MOT || 90 },
    ];

    container.innerHTML = domains.map(d => {
      const pct = Math.max(0, Math.min(100, ((d.score - 20) / 140) * 100));
      const color = d.score < 70 ? "var(--error)" : (d.score < 80 ? "var(--warning)" : "var(--success)");
      return `
        <div style="margin-bottom: 0.85rem;">
          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.25rem;">
            <span>${d.name} (${d.code})</span>
            <span>Sample Mean SS: <strong>${d.score}</strong></span>
          </div>
          <div style="height: 12px; background: #F3F4F6; border-radius: var(--radius-full); position: relative; overflow: hidden; border: 1px solid var(--border-color);">
            <div style="height: 100%; width: ${pct}%; background-color: ${color}; border-radius: var(--radius-full);"></div>
            <div style="position: absolute; top: 0; bottom: 0; left: 57.14%; width: 2px; background: #475569;" title="Population Mean 100"></div>
          </div>
        </div>
      `;
    }).join("");
  },

  async loadRecentAssessments(status = "all") {
    const tbody = document.getElementById("overview-recent-tbody");
    if (!tbody) return;

    try {
      const res = await API.fetchAssessments("", status);
      const items = (res.assessments || []).slice(0, 5);

      if (items.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
              No assessments found for this filter.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = items.map(item => {
        const p = item.patient_info || {};
        const isCompleted = item.status === "Completed";
        const badgeClass = isCompleted ? "badge-completed" : "badge-review";
        const intakeTag = item.intake_method === "document_upload" ? "📄 Document" : "✍️ Manual";
        return `
          <tr>
            <td><strong>${item.assessment_id}</strong></td>
            <td>${p.name || "Unknown"}</td>
            <td>${p.age_years !== undefined ? p.age_years : "—"}y ${p.age_months || 0}m</td>
            <td><span class="badge badge-neutral">${intakeTag}</span></td>
            <td><span class="badge ${badgeClass}">${item.status}</span></td>
            <td>${item.created_at ? item.created_at.slice(0, 10) : "—"}</td>
            <td>
              <div style="display: flex; gap: 0.35rem;">
                <button class="btn btn-outline btn-sm" onclick="App.openAssessmentDetail('${item.assessment_id}');">
                  View
                </button>
                ${item.report_generated ? `
                  <a class="btn btn-primary btn-sm" href="${API.getReportDownloadUrl(item.assessment_id)}" target="_blank">
                    PDF
                  </a>
                ` : ""}
              </div>
            </td>
          </tr>
        `;
      }).join("");

    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--error); padding: 1.5rem;">
            Failed to load assessments: ${err.message}
          </td>
        </tr>
      `;
    }
  },

  async loadHistory(search = "", status = "") {
    const tbody = document.getElementById("history-table-tbody");
    if (!tbody) return;

    try {
      const res = await API.fetchAssessments(search, status);
      const items = res.assessments || [];

      if (items.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" style="text-align: center; color: var(--text-secondary); padding: 2.5rem;">
              No matching records found in clinical assessments registry.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = items.map(item => {
        const p = item.patient_info || {};
        const isCompleted = item.status === "Completed";
        const badgeClass = isCompleted ? "badge-completed" : "badge-review";
        const intakeTag = item.intake_method === "document_upload" ? "Document Upload" : "Manual Form";
        return `
          <tr>
            <td><strong>${item.assessment_id}</strong></td>
            <td>${p.name || "Unknown"}</td>
            <td>${p.age_years !== undefined ? p.age_years : "—"}y ${p.age_months || 0}m</td>
            <td>${p.sex || "—"}</td>
            <td><span class="badge badge-neutral">${intakeTag}</span></td>
            <td><span class="badge ${badgeClass}">${item.status}</span></td>
            <td>${item.created_at ? item.created_at.slice(0, 10) : "—"}</td>
            <td>
              <span class="badge ${item.report_generated ? 'badge-completed' : 'badge-neutral'}">
                ${item.report_generated ? 'Generated' : 'Pending'}
              </span>
            </td>
            <td>
              <div style="display: flex; gap: 0.35rem;">
                <button class="btn btn-outline btn-sm" onclick="App.openAssessmentDetail('${item.assessment_id}');">
                  Open
                </button>
                ${item.report_generated ? `
                  <a class="btn btn-primary btn-sm" href="${API.getReportDownloadUrl(item.assessment_id)}" target="_blank">
                    PDF
                  </a>
                ` : ""}
                <button class="btn btn-ghost btn-sm" onclick="App.deleteAssessmentRecord('${item.assessment_id}');" title="Delete record">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align: center; color: var(--error); padding: 2rem;">
            Error loading directory: ${err.message}
          </td>
        </tr>
      `;
    }
  },

  async loadPatients(search = "") {
    const tbody = document.getElementById("patients-table-tbody");
    if (!tbody) return;

    try {
      const res = await API.fetchPatients(search);
      const patients = res.patients || [];

      if (patients.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; color: var(--text-secondary); padding: 2.5rem;">
              No registered patient records found.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = patients.map(pat => `
        <tr>
          <td><strong>${pat.name}</strong></td>
          <td>${pat.age_years !== undefined ? pat.age_years : "—"}y ${pat.age_months || 0}m</td>
          <td>${pat.sex || "—"}</td>
          <td>${pat.total_assessments}</td>
          <td><strong>${pat.latest_assessment_id || "—"}</strong></td>
          <td><span class="badge badge-completed">${pat.latest_status}</span></td>
          <td><strong>${pat.latest_abc !== "-" ? pat.latest_abc : "—"}</strong></td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="App.startAssessmentForPatient('${pat.name.replace(/'/g, "\\'")}', ${pat.age_years || 7}, ${pat.age_months || 6}, '${pat.sex || 'Male'}');">
              New Evaluation
            </button>
          </td>
        </tr>
      `).join("");

    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--error); padding: 2rem;">
            Error loading patients: ${err.message}
          </td>
        </tr>
      `;
    }
  },

  async loadReports() {
    const tbody = document.getElementById("reports-table-tbody");
    if (!tbody) return;

    try {
      const res = await API.fetchReports();
      const reports = res.reports || [];

      if (reports.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-secondary); padding: 2.5rem;">
              No clinical reports generated yet. Complete an assessment to synthesize and download publication PDFs.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = reports.map(r => `
        <tr>
          <td><strong>${r.assessment_id}</strong></td>
          <td>${r.patient_name}</td>
          <td>${r.date}</td>
          <td><span style="font-family: monospace; font-size: 0.775rem;">${r.pdf_filename}</span></td>
          <td><span class="badge badge-completed">Available</span></td>
          <td>
            <a class="btn btn-primary btn-sm" href="${r.download_url}" target="_blank">
              📥 Download PDF
            </a>
          </td>
        </tr>
      `).join("");

    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--error); padding: 2rem;">
            Error loading reports: ${err.message}
          </td>
        </tr>
      `;
    }
  },

  async loadAnalytics() {
    try {
      const res = await API.fetchAnalytics();
      if (!res.ok || !res.analytics) return;
      const a = res.analytics;

      const setEl = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val !== null && val !== undefined ? val : "—";
      };

      setEl("analytics-completed-val", a.completed_assessments || 0);
      setEl("analytics-ratio-val", `${a.intake_breakdown ? a.intake_breakdown.manual : 0} / ${a.intake_breakdown ? a.intake_breakdown.document_upload : 0}`);
      setEl("analytics-mean-abc-val", (a.average_domain_scores && a.average_domain_scores.ABC) ? a.average_domain_scores.ABC : "—");
      setEl("analytics-reports-val", a.reports_generated || 0);

      const barsContainer = document.getElementById("analytics-domain-bars-container");
      if (barsContainer) {
        const domScores = a.average_domain_scores || {};
        const doms = [
          { code: "COM", name: "Communication", score: domScores.COM || 0 },
          { code: "DLS", name: "Daily Living Skills", score: domScores.DLS || 0 },
          { code: "SOC", name: "Socialization", score: domScores.SOC || 0 },
          { code: "MOT", name: "Motor Skills", score: domScores.MOT || 0 },
        ];

        barsContainer.innerHTML = doms.map(d => {
          const pct = Math.max(0, Math.min(100, ((d.score - 20) / 140) * 100));
          return `
            <div style="margin-bottom: 1.25rem;">
              <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem;">
                <span>${d.name} (${d.code})</span>
                <span>Sample Mean: <strong>${d.score}</strong></span>
              </div>
              <div style="height: 18px; background: #F3F4F6; border-radius: var(--radius-sm); position: relative; overflow: hidden; border: 1px solid var(--border-color);">
                <div style="height: 100%; width: ${pct}%; background-color: var(--accent-yellow); border-radius: var(--radius-sm);"></div>
                <div style="position: absolute; top: 0; bottom: 0; left: 57.14%; width: 2px; background: #475569;" title="Mean 100"></div>
              </div>
            </div>
          `;
        }).join("");
      }

    } catch (e) {
      console.warn("Analytics load error:", e);
    }
  },

  async openAssessmentDetail(assessmentId) {
    try {
      const res = await API.fetchAssessmentDetail(assessmentId);
      if (!res.ok || !res.assessment) {
        Toast.show("Assessment could not be loaded.", "error");
        return;
      }
      const a = res.assessment;

      // Hydrate Wizard state
      Wizard.state.assessment_id = a.assessment_id;
      if (a.patient_info) Wizard.state.patient_info = a.patient_info;
      if (a.raw_scores) Wizard.state.raw_scores = a.raw_scores;
      Wizard.state.verified = Boolean(a.verified);
      Wizard.state.scoring_results = a.scores ? { scores: a.scores, patterns: a.patterns } : null;

      this.navigateTo("new-assessment");

      if (a.scores) {
        Wizard.goToStep(7);
        Toast.show(`Loaded evaluation ${assessmentId}.`, "success");
      } else {
        Wizard.goToStep(4);
        Toast.show(`Opened draft assessment ${assessmentId}.`, "info");
      }
    } catch (err) {
      Toast.show("Failed to load assessment: " + err.message, "error");
    }
  },

  deleteAssessmentRecord(assessmentId) {
    Modal.confirm({
      title: "Delete Clinical Assessment",
      message: `Are you sure you want to permanently delete assessment record ${assessmentId}? This action cannot be undone.`,
      confirmText: "Delete Record",
      onConfirm: async () => {
        try {
          await API.deleteAssessment(assessmentId);
          Toast.show(`Assessment ${assessmentId} deleted.`, "success");
          this.refreshData();
        } catch (err) {
          Toast.show("Delete failed: " + err.message, "error");
        }
      },
    });
  },

  startManualIntake() {
    this.navigateTo("new-assessment");
    Wizard.selectMethod("manual");
    Wizard.goToStep(1);
  },

  startDocumentIntake() {
    this.navigateTo("new-assessment");
    Wizard.selectMethod("document");
    Wizard.goToStep(3);
  },

  startAssessmentForPatient(name, ageY, ageM, sex) {
    this.navigateTo("new-assessment");
    Wizard.state.patient_info.name = name;
    Wizard.state.patient_info.age_years = ageY;
    Wizard.state.patient_info.age_months = ageM;
    Wizard.state.patient_info.sex = sex;
    Wizard.populateStep1();
    Wizard.goToStep(1);
    Toast.show(`Started new assessment for ${name}.`, "info");
  },

  saveSettings() {
    const nameInput = document.getElementById("setting-clinician-name");
    const licInput = document.getElementById("setting-license-id");
    const aiInput = document.getElementById("setting-ai-mode");

    const settings = {
      clinician_name: nameInput ? nameInput.value.trim() : "Dr. Talha Rehman",
      license_id: licInput ? licInput.value.trim() : "PSY-94821-CLINICAL",
      ai_mode: aiInput ? aiInput.value : "offline",
    };

    localStorage.setItem("autism_lens_settings", JSON.stringify(settings));

    // Update profile footer in sidebar
    const profileNameEl = document.querySelector(".sidebar-footer .user-name");
    if (profileNameEl && settings.clinician_name) {
      profileNameEl.textContent = settings.clinician_name;
    }

    Toast.show("Preferences saved successfully.", "success");
  },

  loadSettings() {
    const raw = localStorage.getItem("autism_lens_settings");
    if (!raw) return;

    try {
      const s = JSON.parse(raw);
      const nameInput = document.getElementById("setting-clinician-name");
      const licInput = document.getElementById("setting-license-id");
      const aiInput = document.getElementById("setting-ai-mode");
      const profileNameEl = document.querySelector(".sidebar-footer .user-name");

      if (nameInput && s.clinician_name) nameInput.value = s.clinician_name;
      if (licInput && s.license_id) licInput.value = s.license_id;
      if (aiInput && s.ai_mode) aiInput.value = s.ai_mode;
      if (profileNameEl && s.clinician_name) profileNameEl.textContent = s.clinician_name;

    } catch (e) {
      console.warn("Could not load stored preferences:", e);
    }

    const apiSettingInput = document.getElementById("setting-api-url");
    if (apiSettingInput) {
      apiSettingInput.value = window.location.origin + "/api";
    }
  },

  resetSettings() {
    localStorage.removeItem("autism_lens_settings");
    const nameInput = document.getElementById("setting-clinician-name");
    const licInput = document.getElementById("setting-license-id");
    const aiInput = document.getElementById("setting-ai-mode");
    const profileNameEl = document.querySelector(".sidebar-footer .user-name");

    if (nameInput) nameInput.value = "Dr. Talha Rehman, Clinical Neuropsychologist";
    if (licInput) licInput.value = "PSY-94821-CLINICAL";
    if (aiInput) aiInput.value = "offline";
    if (profileNameEl) profileNameEl.textContent = "Dr. Talha Rehman";

    Toast.show("Settings reset to clinical defaults.", "info");
  },
};

window.App = App;

// Bootstrap application on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
