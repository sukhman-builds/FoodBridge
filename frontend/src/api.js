// Thin client for the FoodBridge backend. Contains no secrets: the base URL is
// public configuration (VITE_API_BASE_URL), never a credential.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const FIELD_LABELS = {
  food_name: 'Food name',
  description: 'Description',
  servings: 'Servings',
  location: 'Pickup location',
  pickup_deadline: 'Pickup window',
  donor_name: 'Donor name',
  donor_contact: 'Contact',
  category: 'Food category',
  claimed_by: 'Organization name',
};

// FastAPI returns either {detail: "text"} or {detail: [{loc, msg}, ...]}.
function messageFromDetail(detail, fallback) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = item.loc && FIELD_LABELS[item.loc[item.loc.length - 1]];
        const msg = String(item.msg || 'is invalid').replace(/^Value error, /, '');
        return field ? `${field}: ${msg}` : msg;
      })
      .join('. ');
  }
  return fallback;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new ApiError(
      'Could not reach the FoodBridge server. Please check that the backend is running and try again.',
      0
    );
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON body; handled below.
  }

  if (!response.ok) {
    throw new ApiError(
      messageFromDetail(data && data.detail, `Request failed (HTTP ${response.status}).`),
      response.status
    );
  }
  return data;
}

export function createDonation(payload) {
  return request('/donations', { method: 'POST', body: JSON.stringify(payload) });
}

export function listDonations({ status = 'available' } = {}) {
  return request(`/donations?status=${encodeURIComponent(status)}`);
}

export function claimDonation(donationId, claimedBy) {
  return request(`/donations/${encodeURIComponent(donationId)}/claim`, {
    method: 'POST',
    body: JSON.stringify({ claimed_by: claimedBy }),
  });
}
