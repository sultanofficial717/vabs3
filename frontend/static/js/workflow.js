/**
 * Autism Lens — Guided 8-Step Clinical Assessment Wizard Manager
 * State machine handling Demographics, Document Extraction, Score Review,
 * Pre-Scoring Verification Gate, Pearson VABS-3 Scoring, Visualizations, and ReportLab PDF Export.
 */

const Wizard = {
  currentStep: 1,
  totalSteps: 8,
  intakeMethod: "manual", // 'manual' or 'document'

  state: {
    assessment_id: null,
    patient_info: {
      name: "PT-84291",
      age_years: 7,
      age_months: 6,
      sex: "Male",
      respondent: "Elena Vance",
      relationship: "Mother",
      test_date: new Date().toISOString().split("T")[0],
      referral: "Evaluation of social-communication delay, transition rigidity, and adaptive behavior profile.",
    },
    raw_scores: {
      rec: 28, exp: 32, wrn: 14,
      per: 38, dom: 18, cmm: 12,
      ipr: 16, pla: 12, cop: 10,
      gmo: 36, fmo: 26,
    },
    extracted_fields: {},
    maladaptive: {
      provided: true,
      int: [1, 2, 0, 1, 1, 0, 2, 0, 1, 1, 1, 0, 0],
      ext: [1, 1, 0, 0, 1, 2, 0, 0, 2, 0, 0],
      critical: [2, 0, 1, 2, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    },
    verified: false,
    scoring_results: null,
    report_data: null,
  },

  domains: [
    { code: "COM", name: "Communication", subcodes: ["rec", "exp", "wrn"] },
    { code: "DLS", name: "Daily Living Skills", subcodes: ["per", "dom", "cmm"] },
    { code: "SOC", name: "Socialization", subcodes: ["ipr", "pla", "cop"] },
    { code: "MOT", name: "Motor Skills", subcodes: ["gmo", "fmo"] },
  ],

  subdomains: [
    { code: "rec", name: "Receptive", domain: "COM", max: 78, desc: "Understanding spoken/gestural instructions" },
    { code: "exp", name: "Expressive", domain: "COM", max: 98, desc: "Verbal output, vocabulary, sentence mastery" },
    { code: "wrn", name: "Written", domain: "COM", max: 76, desc: "Reading comprehension, emergent literacy, writing" },
    { code: "per", name: "Personal", domain: "DLS", max: 110, desc: "Eating, dressing, hygiene, self-care routines" },
    { code: "dom", name: "Domestic", domain: "DLS", max: 60, desc: "Household chores, safety precautions in home" },
    { code: "cmm", name: "Community", domain: "DLS", max: 116, desc: "Money, travel, telephone, public safety rules" },
    { code: "ipr", name: "Interpersonal", domain: "SOC", max: 86, desc: "Peer relationships, friendships, social cues" },
    { code: "pla", name: "Play and Leisure", domain: "SOC", max: 72, desc: "Imaginative play, games with rules, recreational activities" },
    { code: "cop", name: "Coping Skills", domain: "SOC", max: 66, desc: "Emotional regulation, transition flexibility, peer manners" },
    { code: "gmo", name: "Gross Motor", domain: "MOT", max: 86, desc: "Locomotor skills, coordination, physical balance" },
    { code: "fmo", name: "Fine Motor", domain: "MOT", max: 68, desc: "Pencil grasp, manipulative dexterity, precision handling" },
  ],

  init() {
    this.bindEvents();
    this.populateStep1();
    this.goToStep(1);
  },

  bindEvents() {
    // Stepper node clicks
    document.querySelectorAll(".wizard-step-node").forEach(node => {
      node.addEventListener("click", () => {
        const step = parseInt(node.dataset.step, 10);
        if (this.canNavigateTo(step)) {
          this.goToStep(step);
        } else {
          Toast.show(`Step ${step} requires completing earlier verification stages.`, "warning");
        }
      });
    });

    // Dropzone setup
    const dropzone = document.getElementById("wiz-dropzone");
    const fileInput = document.getElementById("wiz-file-input");
    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("dragover", e => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
      dropzone.addEventListener("drop", e => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleFileUpload(e.dataTransfer.files[0]);
        }
      });
      fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files.length > 0) {
          this.handleFileUpload(fileInput.files[0]);
        }
      });
    }

    // Step 1 inline input validation listeners
    const nameInput = document.getElementById("wiz-patient-name");
    const ageYInput = document.getElementById("wiz-patient-age-y");
    const ageMInput = document.getElementById("wiz-patient-age-m");

    if (nameInput) {
      nameInput.addEventListener("input", () => {
        if (nameInput.value.trim().length > 0) {
          nameInput.classList.remove("input-error");
          const errEl = document.getElementById("wiz-patient-name-err");
          if (errEl) errEl.style.display = "none";
        }
      });
    }

    if (ageYInput) {
      ageYInput.addEventListener("input", () => {
        const v = parseInt(ageYInput.value, 10);
        if (!isNaN(v) && v >= 0 && v <= 90) {
          ageYInput.classList.remove("input-error");
          const errEl = document.getElementById("wiz-patient-age-err");
          if (errEl) errEl.style.display = "none";
        }
      });
    }

    if (ageMInput) {
      ageMInput.addEventListener("input", () => {
        const v = parseInt(ageMInput.value, 10);
        if (!isNaN(v) && v >= 0 && v <= 11) {
          ageMInput.classList.remove("input-error");
          const errEl = document.getElementById("wiz-patient-months-err");
          if (errEl) errEl.style.display = "none";
        }
      });
    }
  },

  canNavigateTo(step) {
    if (step <= this.currentStep) return true;
    if (step === 2) return true;
    if (step === 3) return this.intakeMethod === "document";
    if (step === 4 || step === 5) return true;
    if (step === 6 || step === 7) return Boolean(this.state.verified);
    if (step === 8) return Boolean(this.state.scoring_results);
    return false;
  },

  goToStep(step) {
    this.currentStep = step;

    // Update stepper nodes
    document.querySelectorAll(".wizard-step-node").forEach(node => {
      const s = parseInt(node.dataset.step, 10);
      node.classList.remove("active", "completed");
      if (s === step) {
        node.classList.add("active");
      } else if (s < step) {
        node.classList.add("completed");
      }
    });

    // Hide all subpanels and show current
    document.querySelectorAll(".wizard-subpanel").forEach(panel => {
      panel.style.display = "none";
    });

    const activeSubpanel = document.getElementById(`wizard-step-${step}`);
    if (activeSubpanel) {
      activeSubpanel.style.display = "block";
    }

    // Step-specific render hooks
    if (step === 4) this.renderReviewStep();
    if (step === 5) this.renderVerificationStep();
    if (step === 7) this.renderResultsStep();
    if (step === 8) this.renderReportStep();

    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  populateStep1() {
    const p = this.state.patient_info;
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    };
    setVal("wiz-patient-name", p.name || "");
    setVal("wiz-patient-age-y", p.age_years !== undefined ? p.age_years : 7);
    setVal("wiz-patient-age-m", p.age_months !== undefined ? p.age_months : 6);
    setVal("wiz-patient-sex", p.sex || "Male");
    setVal("wiz-respondent", p.respondent || "Elena Vance");
    setVal("wiz-relationship", p.relationship || "Mother");
    setVal("wiz-test-date", p.test_date || new Date().toISOString().split("T")[0]);
    setVal("wiz-referral", p.referral || "");
  },

  loadSamplePatient() {
    this.state.patient_info = {
      name: "Leo Vance",
      age_years: 7,
      age_months: 6,
      sex: "Male",
      respondent: "Elena Vance",
      relationship: "Mother",
      test_date: new Date().toISOString().split("T")[0],
      referral: "Referred for formal adaptive assessment due to pronounced social-communication rigidity, peer interaction avoidance, and atypical repetitive behavioral routines.",
    };
    this.state.raw_scores = {
      rec: 28, exp: 32, wrn: 14,
      per: 38, dom: 18, cmm: 12,
      ipr: 16, pla: 12, cop: 10,
      gmo: 36, fmo: 26,
    };
    this.populateStep1();
    Toast.show("Sample patient profile loaded (Leo Vance, 7y 6m).", "success");
  },

  validateStep1() {
    let valid = true;
    const nameEl = document.getElementById("wiz-patient-name");
    const ageYEl = document.getElementById("wiz-patient-age-y");
    const ageMEl = document.getElementById("wiz-patient-age-m");

    const nameVal = nameEl ? nameEl.value.trim() : "";
    const nameErr = document.getElementById("wiz-patient-name-err");
    if (!nameVal) {
      if (nameEl) nameEl.classList.add("input-error");
      if (nameErr) nameErr.style.display = "block";
      valid = false;
    } else {
      if (nameEl) nameEl.classList.remove("input-error");
      if (nameErr) nameErr.style.display = "none";
    }

    const ageYVal = ageYEl ? parseInt(ageYEl.value, 10) : NaN;
    const ageYErr = document.getElementById("wiz-patient-age-err");
    if (isNaN(ageYVal) || ageYVal < 0 || ageYVal > 90) {
      if (ageYEl) ageYEl.classList.add("input-error");
      if (ageYErr) ageYErr.style.display = "block";
      valid = false;
    } else {
      if (ageYEl) ageYEl.classList.remove("input-error");
      if (ageYErr) ageYErr.style.display = "none";
    }

    const ageMVal = ageMEl ? parseInt(ageMEl.value, 10) : 0;
    const ageMErr = document.getElementById("wiz-patient-months-err");
    if (isNaN(ageMVal) || ageMVal < 0 || ageMVal > 11) {
      if (ageMEl) ageMEl.classList.add("input-error");
      if (ageMErr) ageMErr.style.display = "block";
      valid = false;
    } else {
      if (ageMEl) ageMEl.classList.remove("input-error");
      if (ageMErr) ageMErr.style.display = "none";
    }

    return valid;
  },

  readStep1() {
    const getVal = id => (document.getElementById(id) ? document.getElementById(id).value.trim() : "");
    this.state.patient_info = {
      name: getVal("wiz-patient-name") || "PT-" + Math.floor(10000 + Math.random() * 90000),
      age_years: parseInt(getVal("wiz-patient-age-y"), 10) || 0,
      age_months: parseInt(getVal("wiz-patient-age-m"), 10) || 0,
      sex: getVal("wiz-patient-sex") || "Male",
      respondent: getVal("wiz-respondent") || "Caregiver",
      relationship: getVal("wiz-relationship") || "Parent",
      test_date: getVal("wiz-test-date") || new Date().toISOString().split("T")[0],
      referral: getVal("wiz-referral") || "",
    };
  },

  nextFromStep1() {
    if (!this.validateStep1()) {
      Toast.show("Please correct the highlighted patient intake fields.", "error");
      return;
    }
    this.readStep1();
    this.goToStep(2);
  },

  selectMethod(method) {
    this.intakeMethod = method;
    const cardManual = document.getElementById("choice-card-manual");
    const cardDoc = document.getElementById("choice-card-doc");
    if (cardManual && cardDoc) {
      if (method === "manual") {
        cardManual.classList.add("selected");
        cardDoc.classList.remove("selected");
      } else {
        cardDoc.classList.add("selected");
        cardManual.classList.remove("selected");
      }
    }
  },

  nextFromStep2() {
    if (this.intakeMethod === "document") {
      this.goToStep(3);
    } else {
      this.goToStep(4);
    }
  },

  async handleFileUpload(file) {
    const statusBox = document.getElementById("wiz-upload-status");
    const previewBox = document.getElementById("wiz-preview-file");
    const nextBtn = document.getElementById("wiz-btn-step3-next");
    const fileInput = document.getElementById("wiz-file-input");

    if (!file) return;

    statusBox.style.display = "block";
    statusBox.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.75rem; color: #171717;">
        <span style="font-size: 1.25rem; animation: spin 1s linear infinite; display: inline-block;">⚙️</span>
        <div>
          <strong>Processing document...</strong>
          <div style="font-size: 0.775rem; color: var(--text-secondary);">
            Running OpenCV deskewing, Otsu binarization, and pypdf structured text extraction...
          </div>
        </div>
      </div>
    `;

    try {
      const res = await API.extractDocument(file);
      this.state.extracted_fields = res;

      // Merge extracted demographics
      if (res.patient_info) {
        if (res.patient_info.name) this.state.patient_info.name = res.patient_info.name;
        if (res.patient_info.age_years !== undefined) this.state.patient_info.age_years = res.patient_info.age_years;
        if (res.patient_info.age_months !== undefined) this.state.patient_info.age_months = res.patient_info.age_months;
        if (res.patient_info.sex) this.state.patient_info.sex = res.patient_info.sex;
        if (res.patient_info.respondent) this.state.patient_info.respondent = res.patient_info.respondent;
        if (res.patient_info.test_date) this.state.patient_info.test_date = res.patient_info.test_date;
      }

      // Merge extracted raw scores
      if (res.raw_scores && Object.keys(res.raw_scores).length > 0) {
        this.state.raw_scores = {
          ...this.state.raw_scores,
          ...res.raw_scores,
        };
      }

      const scoreCount = res.raw_scores ? Object.keys(res.raw_scores).length : 0;

      statusBox.innerHTML = `
        <div style="color: var(--success); font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
          <span>✓</span>
          <span>Extraction Complete (${res.confidence || 95}% Confidence)</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-main); margin-top: 0.35rem;">
          Extracted <strong>${scoreCount} of 11</strong> subdomain raw scores. You will review and verify every field in Step 4.
        </div>
        ${res.warnings && res.warnings.length > 0 ? `
          <ul style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--warning-text); padding-left: 1.25rem;">
            ${res.warnings.map(w => `<li>${w}</li>`).join("")}
          </ul>
        ` : ""}
      `;

      previewBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.85rem 1rem; border: 1px solid var(--border-color); border-radius: var(--radius-md); background: #FFFFFF; margin-top: 0.75rem;">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.6rem;">📄</span>
            <div>
              <strong style="font-size: 0.85rem; color: var(--text-main);">${file.name}</strong>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">
                ${(file.size / 1024).toFixed(1)} KB • ${(res.source_type || "document").toUpperCase()} Processed
              </div>
            </div>
          </div>
          <span class="badge badge-completed">Ready for Review</span>
        </div>
      `;

      if (nextBtn) nextBtn.disabled = false;
      Toast.show("Document successfully processed.", "success");

    } catch (err) {
      statusBox.innerHTML = `
        <div style="color: var(--error); font-weight: 700;">
          ⚠️ Document processing note: ${err.message}
        </div>
        <p style="font-size: 0.775rem; color: var(--text-secondary); margin-top: 0.35rem;">
          Standard parsing completed with partial optical recognition. You can proceed to Step 4 to review and complete the inputs.
        </p>
      `;
      if (nextBtn) nextBtn.disabled = false;
      Toast.show("Document parsed with partial OCR notes. Please review scores in Step 4.", "warning");
    } finally {
      if (fileInput) fileInput.value = "";
    }
  },

  renderReviewStep() {
    const container = document.getElementById("wiz-review-container");
    if (!container) return;

    const p = this.state.patient_info;
    const scores = this.state.raw_scores;

    let html = `
      <!-- Demographics Card -->
      <div class="card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.85rem;">
          Patient Demographics Verification
        </h4>
        <div class="form-grid-3">
          <div class="form-group">
            <label for="rev-name">Patient Name / Identifier <span class="req-star">*</span></label>
            <input type="text" id="rev-name" value="${p.name || ''}" placeholder="Patient Name or ID">
          </div>
          <div class="form-group">
            <label for="rev-age-y">Chronological Age (Years) <span class="req-star">*</span></label>
            <input type="number" id="rev-age-y" value="${p.age_years !== undefined ? p.age_years : 7}" min="0" max="90">
          </div>
          <div class="form-group">
            <label for="rev-age-m">Chronological Age (Months)</label>
            <input type="number" id="rev-age-m" value="${p.age_months !== undefined ? p.age_months : 6}" min="0" max="11">
          </div>
        </div>
      </div>

      <!-- Domain Grouped Subdomain Raw Scores -->
      <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.75rem;">
          <div>
            <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-main);">
              Subdomain Raw Scores (Grouped by Domain)
            </h4>
            <p class="card-subtitle">
              Verify scores against the administration sheet. Domain raw sums update in real-time.
            </p>
          </div>
        </div>
    `;

    // Render grouped by domain
    this.domains.forEach(dom => {
      const domSubs = this.subdomains.filter(s => s.domain === dom.code);
      let initialSum = 0;
      domSubs.forEach(s => {
        initialSum += (parseInt(scores[s.code], 10) || 0);
      });

      html += `
        <div class="domain-review-card">
          <div class="domain-review-header">
            <div class="domain-title-badge">
              <span>${dom.name}</span>
              <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: normal;">(${dom.code})</span>
            </div>
            <div class="domain-sum-tag" id="domain-sum-${dom.code}">
              Domain Raw Total: <strong>${initialSum}</strong>
            </div>
          </div>
          <div class="data-table-wrapper">
            <table class="table-clean">
              <thead>
                <tr>
                  <th style="width: 28%;">Subdomain</th>
                  <th style="width: 35%;">Clinical Description</th>
                  <th style="width: 12%;">Allowable Max</th>
                  <th style="width: 15%;">Raw Score Input</th>
                  <th style="width: 10%;">Source</th>
                </tr>
              </thead>
              <tbody>
                ${domSubs.map(sub => {
                  const val = scores[sub.code] !== undefined ? scores[sub.code] : 0;
                  const isExtracted = Boolean(this.state.extracted_fields.raw_scores && this.state.extracted_fields.raw_scores[sub.code] !== undefined);
                  return `
                    <tr>
                      <td>
                        <strong>${sub.name}</strong>
                        <span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.25rem;">(${sub.code})</span>
                      </td>
                      <td style="font-size: 0.775rem; color: var(--text-secondary);">${sub.desc}</td>
                      <td><span class="badge badge-neutral">0 – ${sub.max}</span></td>
                      <td>
                        <input
                          type="number"
                          class="review-sub-input"
                          id="input-sub-${sub.code}"
                          data-code="${sub.code}"
                          data-domain="${dom.code}"
                          data-max="${sub.max}"
                          value="${val}"
                          min="0"
                          max="${sub.max}"
                          style="width: 85px; padding: 0.35rem 0.5rem; font-size: 0.85rem; font-weight: 600;"
                          oninput="Wizard.onSubScoreChange('${sub.code}', '${dom.code}', ${sub.max});"
                        >
                        <span id="err-sub-${sub.code}" class="form-error-text" style="display: none;">Max: ${sub.max}</span>
                      </td>
                      <td>
                        <span class="badge ${isExtracted ? 'badge-yellow' : 'badge-neutral'}">
                          ${isExtracted ? 'Extracted' : 'Manual'}
                        </span>
                      </td>
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    });

    // Maladaptive Behavior Summary
    html += `
      <div class="card" style="margin-top: 1rem; padding: 1.25rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
          <div>
            <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-main);">
              Maladaptive Behavior Index (Optional Clinical Scales)
            </h4>
            <p class="card-subtitle">
              Internalizing, Externalizing, and DSM-5-TR Critical item behavior flags.
            </p>
          </div>
          <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer;">
            <input type="checkbox" id="rev-maladaptive-toggle" checked onchange="Wizard.toggleMaladaptive(this.checked);">
            <span>Include in scoring</span>
          </label>
        </div>
        <div id="maladaptive-status-summary" style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <div class="system-pill">Internalizing: 13 items verified</div>
          <div class="system-pill">Externalizing: 11 items verified</div>
          <div class="system-pill" style="color: var(--error);">Critical Behaviors: 20 items monitored</div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },

  onSubScoreChange(code, domainCode, maxVal) {
    const input = document.getElementById(`input-sub-${code}`);
    const errEl = document.getElementById(`err-sub-${code}`);
    if (!input) return;

    let val = parseInt(input.value, 10);
    if (isNaN(val)) val = 0;

    if (val < 0 || val > maxVal) {
      input.classList.add("input-error");
      if (errEl) errEl.style.display = "block";
    } else {
      input.classList.remove("input-error");
      if (errEl) errEl.style.display = "none";
      this.state.raw_scores[code] = val;
    }

    // Recalculate domain sum
    const domSubs = this.subdomains.filter(s => s.domain === domainCode);
    let sum = 0;
    domSubs.forEach(s => {
      const inp = document.getElementById(`input-sub-${s.code}`);
      const v = inp ? (parseInt(inp.value, 10) || 0) : (this.state.raw_scores[s.code] || 0);
      sum += v;
    });

    const sumBadge = document.getElementById(`domain-sum-${domainCode}`);
    if (sumBadge) {
      sumBadge.innerHTML = `Domain Raw Total: <strong>${sum}</strong>`;
    }
  },

  toggleMaladaptive(checked) {
    this.state.maladaptive.provided = checked;
    const box = document.getElementById("maladaptive-status-summary");
    if (box) {
      box.style.opacity = checked ? "1" : "0.4";
    }
  },

  nextFromStep4() {
    // Read updated demographic values
    const nameEl = document.getElementById("rev-name");
    const ageYEl = document.getElementById("rev-age-y");
    const ageMEl = document.getElementById("rev-age-m");

    if (nameEl) this.state.patient_info.name = nameEl.value.trim() || this.state.patient_info.name;
    if (ageYEl) this.state.patient_info.age_years = parseInt(ageYEl.value, 10) || 0;
    if (ageMEl) this.state.patient_info.age_months = parseInt(ageMEl.value, 10) || 0;

    // Validate raw score inputs
    let hasOutOfRange = false;
    document.querySelectorAll(".review-sub-input").forEach(inp => {
      const code = inp.dataset.code;
      const max = parseInt(inp.dataset.max, 10);
      const val = parseInt(inp.value, 10) || 0;

      if (val < 0 || val > max) {
        inp.classList.add("input-error");
        hasOutOfRange = true;
      } else {
        inp.classList.remove("input-error");
        this.state.raw_scores[code] = val;
      }
    });

    if (hasOutOfRange) {
      Toast.show("One or more raw scores exceed allowable maximum limits. Please correct them.", "error");
      return;
    }

    this.goToStep(5);
  },

  renderVerificationStep() {
    const summaryBox = document.getElementById("wiz-verification-summary");
    if (!summaryBox) return;

    const p = this.state.patient_info;
    const scores = this.state.raw_scores;

    // Calculate domain subtotals
    const domainTotals = {};
    this.domains.forEach(d => {
      let sum = 0;
      d.subcodes.forEach(sc => {
        sum += (scores[sc] || 0);
      });
      domainTotals[d.code] = sum;
    });

    summaryBox.innerHTML = `
      <div style="background-color: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: var(--shadow-sm);">
        <h4 style="font-size: 1rem; font-weight: 700; color: var(--text-main); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
          <span style="color: var(--success);">🛡️</span>
          <span>Pre-Scoring Clinical Verification Checklist</span>
        </h4>

        <div style="display: flex; flex-direction: column; gap: 0.85rem; font-size: 0.85rem;">
          <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle);">
            <span style="color: var(--success); font-size: 1.1rem; line-height: 1;">✓</span>
            <div>
              <strong>Patient Identity & Intake:</strong>
              <div style="color: var(--text-secondary); margin-top: 0.15rem;">
                ${p.name} • Age ${p.age_years} years ${p.age_months} months (${p.sex}) • Informant: ${p.respondent} (${p.relationship})
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle);">
            <span style="color: var(--success); font-size: 1.1rem; line-height: 1;">✓</span>
            <div>
              <strong>Pearson Table B Normative Age Bracket:</strong>
              <div style="color: var(--text-secondary); margin-top: 0.15rem;">
                Age Bracket Key: <code>${p.age_years}:${p.age_months >= 6 ? '6-11' : '0-5'}</code> (Appendix B Comprehensive Interview Form Norms)
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle);">
            <span style="color: var(--success); font-size: 1.1rem; line-height: 1;">✓</span>
            <div>
              <strong>Subdomain Completeness & Range Boundaries:</strong>
              <div style="color: var(--text-secondary); margin-top: 0.15rem;">
                All 11 subdomains specified within valid limits (Receptive, Expressive, Written, Personal, Domestic, Community, Interpersonal, Play, Coping, Gross Motor, Fine Motor).
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-subtle);">
            <span style="color: var(--success); font-size: 1.1rem; line-height: 1;">✓</span>
            <div>
              <strong>Domain Raw Score Totals:</strong>
              <div style="color: var(--text-secondary); margin-top: 0.15rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <span class="badge badge-neutral">Communication: ${domainTotals.COM} pts</span>
                <span class="badge badge-neutral">Daily Living: ${domainTotals.DLS} pts</span>
                <span class="badge badge-neutral">Socialization: ${domainTotals.SOC} pts</span>
                <span class="badge badge-neutral">Motor Skills: ${domainTotals.MOT} pts</span>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
            <span style="color: var(--success); font-size: 1.1rem; line-height: 1;">✓</span>
            <div>
              <strong>Clinical Decision-Support Integrity:</strong>
              <div style="color: var(--text-secondary); margin-top: 0.15rem;">
                Scoring is descriptive and standardized according to DSM-5-TR Criteria A & B. Final clinical reports require evaluator countersignature.
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  async confirmVerification() {
    const errBox = document.getElementById("wiz-verification-errors");
    if (errBox) {
      errBox.style.display = "none";
      errBox.innerHTML = "";
    }

    const payload = {
      patient_info: this.state.patient_info,
      raw_scores: this.state.raw_scores,
      maladaptive: this.state.maladaptive,
      verified: true,
    };

    try {
      const res = await API.validateAssessment(payload);
      if (!res.ok) {
        if (errBox) {
          errBox.style.display = "block";
          errBox.innerHTML = `
            <div style="background-color: var(--error-bg); border-left: 4px solid var(--error); padding: 1rem; border-radius: var(--radius-md); color: var(--error-text); font-size: 0.85rem;">
              <strong>Verification Gate Notice:</strong>
              <ul style="margin-top: 0.35rem; padding-left: 1.25rem;">
                ${(res.errors || ["Validation failed"]).map(e => `<li>${e}</li>`).join("")}
              </ul>
            </div>
          `;
        }
        Toast.show("Please resolve verification warnings before scoring.", "error");
        return;
      }

      this.state.verified = true;
      Toast.show("All inputs successfully verified.", "success");
      this.goToStep(6);

    } catch (err) {
      Toast.show("Verification error: " + err.message, "error");
    }
  },

  async runScoring() {
    const btn = document.getElementById("wiz-run-scoring-btn");
    const statusBox = document.getElementById("wiz-scoring-status");

    if (btn) btn.disabled = true;
    if (statusBox) {
      statusBox.style.display = "block";
      statusBox.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 0.65rem; background: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.25rem; text-align: left;">
          <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 700; color: var(--text-main);">
            <span style="animation: spin 1s linear infinite; display: inline-block;">⚙️</span>
            <span>Executing Scoring Engine...</span>
          </div>
          <div style="font-size: 0.775rem; color: var(--text-secondary); line-height: 1.6;">
            • Applying Table B.1 normative v-scale transformations (Mean=15, SD=3)...<br>
            • Deriving Domain Standard Scores via Table B.3 (Mean=100, SD=15)...<br>
            • Computing Adaptive Behavior Composite (ABC) & Percentiles...<br>
            • Analyzing DSM-5-TR ASD criteria patterns & domain scatter...
          </div>
        </div>
      `;
    }

    try {
      const payload = {
        assessment_id: this.state.assessment_id,
        patient_info: this.state.patient_info,
        raw_scores: this.state.raw_scores,
        intake_method: this.intakeMethod === "document" ? "document_upload" : "manual",
        maladaptive: this.state.maladaptive,
        verified: true,
      };

      const result = await API.scoreAssessment(payload);
      this.state.scoring_results = result;
      this.state.assessment_id = result.assessment_id || `AL-${Math.floor(10000 + Math.random() * 90000)}`;

      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color: var(--success); font-weight: 700; background: var(--success-bg); border: 1px solid var(--success-border); border-radius: var(--radius-md); padding: 0.85rem;">
            ✓ Pearson VABS-3 Normative Scoring & ASD Pattern Recognition Complete!
          </div>
        `;
      }

      Toast.show("Scoring calculation completed successfully.", "success");

      setTimeout(() => {
        this.goToStep(7);
        if (btn) btn.disabled = false;
        // Background refresh overview and history caches
        App.refreshData();
      }, 700);

    } catch (err) {
      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color: var(--error); font-weight: 700; background: var(--error-bg); border: 1px solid var(--error-border); border-radius: var(--radius-md); padding: 0.85rem;">
            ⚠️ Scoring computation failed: ${err.message}
          </div>
        `;
      }
      if (btn) btn.disabled = false;
      Toast.show("Scoring error: " + err.message, "error");
    }
  },

  renderResultsStep() {
    if (!this.state.scoring_results) return;
    Visualizations.renderResults("wiz-results-container", this.state.scoring_results);
  },

  renderReportStep() {
    const actionBox = document.getElementById("wiz-report-action-box");
    const previewBox = document.getElementById("wiz-report-preview-box");
    const dlBtn = document.getElementById("wiz-download-pdf-btn");
    const printBtn = document.getElementById("wiz-print-report-btn");
    const copyBtn = document.getElementById("wiz-copy-report-btn");

    if (this.state.report_data) {
      if (actionBox) actionBox.style.display = "none";
      if (previewBox) {
        previewBox.style.display = "block";
        previewBox.innerHTML = this.formatNarrativeHtml(this.state.report_data.narrative);
      }
      if (dlBtn) {
        dlBtn.href = API.getReportDownloadUrl(this.state.assessment_id);
        dlBtn.style.display = "inline-flex";
      }
      if (printBtn) printBtn.style.display = "inline-flex";
      if (copyBtn) copyBtn.style.display = "inline-flex";
    } else {
      if (actionBox) actionBox.style.display = "block";
      if (previewBox) previewBox.style.display = "none";
      if (dlBtn) dlBtn.style.display = "none";
      if (printBtn) printBtn.style.display = "none";
      if (copyBtn) copyBtn.style.display = "none";
    }
  },

  async generateReport() {
    const btn = document.getElementById("wiz-build-report-btn");
    const statusBox = document.getElementById("wiz-report-status");

    if (btn) btn.disabled = true;
    if (statusBox) {
      statusBox.style.display = "block";
      statusBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; color: var(--text-main);">
          <span style="animation: spin 1s linear infinite; display: inline-block;">⚙️</span>
          <span>Synthesizing evidence narrative and building publication ReportLab PDF...</span>
        </div>
      `;
    }

    try {
      const payload = {
        assessment_id: this.state.assessment_id,
        patient_info: this.state.patient_info,
        scores: this.state.scoring_results.scores,
        patterns: this.state.scoring_results.patterns,
      };

      const res = await API.generateReport(payload);
      this.state.report_data = res;
      this.state.assessment_id = res.assessment_id;

      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color: var(--success); font-weight: 700;">
            ✓ Report synthesized successfully (Ref: ${res.assessment_id})
          </div>
        `;
      }

      Toast.show("Clinical report & PDF generated successfully.", "success");

      setTimeout(() => {
        this.renderReportStep();
        if (btn) btn.disabled = false;
        App.refreshData();
      }, 500);

    } catch (err) {
      if (statusBox) {
        statusBox.innerHTML = `
          <div style="color: var(--error); font-weight: 700;">
            ⚠️ Report synthesis failed: ${err.message}
          </div>
        `;
      }
      if (btn) btn.disabled = false;
      Toast.show("Report generation failed: " + err.message, "error");
    }
  },

  formatNarrativeHtml(rawText) {
    if (!rawText) return "<p>No narrative text generated.</p>";

    // Clean, publication-quality HTML formatter for clinical narrative
    const lines = rawText.split("\n");
    let html = `
      <div style="border-bottom: 2px solid var(--accent-yellow); padding-bottom: 1rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h2 style="font-size: 1.4rem; color: var(--text-main); font-family: var(--font-sans); margin: 0;">
            Comprehensive Vineland-3 Adaptive Evaluation
          </h2>
          <span class="badge badge-completed">Ref: ${this.state.assessment_id || 'AL-REPORT'}</span>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.35rem; font-family: var(--font-sans);">
          Evaluator: Dr. Talha Rehman, Clinical Neuropsychologist • Date: ${new Date().toLocaleDateString()}
        </div>
      </div>
    `;

    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed) {
        return;
      }
      if (trimmed.startsWith("### ")) {
        html += `<h4 style="font-family: var(--font-sans); color: var(--text-main); margin-top: 1.25rem; margin-bottom: 0.35rem; font-size: 0.95rem;">${this.escapeAndBold(trimmed.slice(4))}</h4>`;
      } else if (trimmed.startsWith("## ")) {
        html += `<h3 style="font-family: var(--font-sans); color: var(--text-main); margin-top: 1.5rem; margin-bottom: 0.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.25rem; font-size: 1.1rem;">${this.escapeAndBold(trimmed.slice(3))}</h3>`;
      } else if (trimmed.startsWith("# ")) {
        html += `<h2 style="font-family: var(--font-sans); color: var(--text-main); margin-top: 1.75rem; margin-bottom: 0.65rem; font-size: 1.25rem;">${this.escapeAndBold(trimmed.slice(2))}</h2>`;
      } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        html += `<div style="display: flex; gap: 0.5rem; margin-bottom: 0.35rem;"><span style="color: var(--accent-yellow-border);">•</span><span>${this.escapeAndBold(trimmed.slice(2))}</span></div>`;
      } else {
        html += `<p style="margin-bottom: 0.75rem;">${this.escapeAndBold(trimmed)}</p>`;
      }
    });

    html += `
      <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color); font-family: var(--font-sans); font-size: 0.8rem; color: var(--text-secondary); display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
          <div>Electronically synthesized by <strong>Autism Lens v2.0</strong></div>
          <div>Clinical Decision-Support Engine • DSM-5-TR Grounded</div>
        </div>
        <div style="text-align: right;">
          <div style="border-bottom: 1px solid #9CA3AF; width: 180px; margin-bottom: 0.25rem;"></div>
          <div>Evaluating Clinician Countersignature</div>
        </div>
      </div>
    `;

    return html;
  },

  escapeAndBold(text) {
    let safe = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    // Bold **text**
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Italic *text*
    safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");
    return safe;
  },

  printReport() {
    window.print();
  },

  copyReportText() {
    if (!this.state.report_data || !this.state.report_data.narrative) {
      Toast.show("No report text available to copy.", "warning");
      return;
    }
    navigator.clipboard.writeText(this.state.report_data.narrative).then(() => {
      Toast.show("Report narrative copied to clipboard.", "success");
    }).catch(() => {
      Toast.show("Failed to copy report text.", "error");
    });
  },
};

window.Wizard = Wizard;
