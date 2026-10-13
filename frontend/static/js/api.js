/**
 * Autism Lens - REST API Service Layer
 * Encapsulates all communications with the Flask backend.
 */
const API = {
  baseUrl: window.location.origin,

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`);
      return await res.json();
    } catch (err) {
      console.error("Health check error:", err);
      return { status: "offline", error: err.message };
    }
  },

  async fetchMetadata() {
    const res = await fetch(`${this.baseUrl}/api/meta`);
    if (!res.ok) {
      throw new Error(`Failed to load assessment metadata: ${res.statusText}`);
    }
    return await res.json();
  },

  async fetchAssessments(search = "", status = "") {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (status) params.append("status", status);
    const res = await fetch(`${this.baseUrl}/api/assessments?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load assessments directory");
    return await res.json();
  },

  async fetchAssessmentDetail(assessmentId) {
    const res = await fetch(`${this.baseUrl}/api/assessments/${encodeURIComponent(assessmentId)}`);
    if (!res.ok) throw new Error("Failed to load assessment detail");
    return await res.json();
  },

  async deleteAssessment(assessmentId) {
    const res = await fetch(`${this.baseUrl}/api/assessments/${encodeURIComponent(assessmentId)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete assessment");
    return await res.json();
  },

  async fetchPatients(search = "") {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    const res = await fetch(`${this.baseUrl}/api/patients?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load patient records");
    return await res.json();
  },

  async fetchReports() {
    const res = await fetch(`${this.baseUrl}/api/reports`);
    if (!res.ok) throw new Error("Failed to load reports catalog");
    return await res.json();
  },

  async fetchAnalytics() {
    const res = await fetch(`${this.baseUrl}/api/analytics`);
    if (!res.ok) throw new Error("Failed to load analytics metrics");
    return await res.json();
  },

  async extractDocument(file, onProgress = null) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${this.baseUrl}/api/documents/extract`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Document extraction failed.");
    }
    return data;
  },

  async validateAssessment(payload) {
    const res = await fetch(`${this.baseUrl}/api/assessments/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      return { ok: false, errors: data.errors || [data.error || "Validation failed"] };
    }
    return data;
  },

  async scoreAssessment(payload) {
    const res = await fetch(`${this.baseUrl}/api/assessments/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Scoring calculation failed.");
    }
    return data;
  },

  async generateReport(payload) {
    const res = await fetch(`${this.baseUrl}/api/assessments/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Report generation failed.");
    }
    return data;
  },

  getReportDownloadUrl(assessmentId) {
    return `${this.baseUrl}/api/assessments/${encodeURIComponent(assessmentId)}/report`;
  },
};

window.API = API;
