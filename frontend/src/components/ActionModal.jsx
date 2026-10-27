import React, { useCallback, useEffect, useState } from 'react';
import { X, HeartHandshake, Search, MapPin, Clock, CheckCircle2, AlertCircle, Sparkles, RefreshCw } from 'lucide-react';
import { createDonation, listDonations, claimDonation } from '../api';
import './ActionModal.css';

// The form offers relative pickup windows; the API stores an absolute deadline.
function deadlineFor(option, now = new Date()) {
  const d = new Date(now);
  switch (option) {
    case 'Within 1 hour':
      d.setHours(d.getHours() + 1);
      break;
    case 'Within 2 hours':
      d.setHours(d.getHours() + 2);
      break;
    case 'This afternoon':
      d.setHours(17, 0, 0, 0);
      break;
    case 'Tonight before 10pm':
      d.setHours(22, 0, 0, 0);
      break;
    default:
      d.setHours(d.getHours() + 2);
  }
  return d;
}

function formatDeadline(iso) {
  return new Date(iso).toLocaleString([], {
    weekday: 'short',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function DonateView({ onClose }) {
  const [status, setStatus] = useState('idle'); // idle | submitting | success
  const [error, setError] = useState('');
  const [created, setCreated] = useState(null);
  const [formData, setFormData] = useState({
    businessName: '',
    foodName: '',
    description: '',
    foodType: 'Prepared Meals',
    servings: '',
    location: '',
    pickupWindow: 'Within 2 hours',
    contact: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const deadline = deadlineFor(formData.pickupWindow);
    if (deadline <= new Date()) {
      setError('That pickup window has already passed today. Please choose a later window.');
      return;
    }

    setStatus('submitting');
    try {
      const donation = await createDonation({
        food_name: formData.foodName,
        description: formData.description,
        servings: Number(formData.servings),
        location: formData.location,
        pickup_deadline: deadline.toISOString(),
        donor_name: formData.businessName,
        donor_contact: formData.contact,
        category: formData.foodType,
      });
      setCreated(donation);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('idle');
    }
  };

  return (
    <div className="modal-body">
      <div className="modal-header">
        <div className="modal-icon-wrap donate">
          <HeartHandshake size={24} />
        </div>
        <div>
          <h3 id="modal-title" className="modal-title">Donate Surplus Food</h3>
          <p className="modal-subtitle">List your surplus so NGOs can reserve it for pickup</p>
        </div>
      </div>

      {status === 'success' ? (
        <div className="modal-success-box" role="status">
          <CheckCircle2 size={48} className="success-icon" />
          <h4>Donation Listed!</h4>
          <p>
            Your listing is now visible to NGOs using FoodBridge. It will be marked as
            claimed once an organization reserves it. No notifications are sent in this
            version, so NGOs find it by browsing the listings.
          </p>
          <div className="success-summary">
            <strong>Listed:</strong> {created.servings} servings of {created.food_name}
          </div>
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="businessName">Donor / Business Name</label>
            <input
              id="businessName"
              name="businessName"
              type="text"
              required
              maxLength={120}
              placeholder="e.g. Blue Bistro, Central Bakery"
              value={formData.businessName}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="foodName">Food Item</label>
            <input
              id="foodName"
              name="foodName"
              type="text"
              required
              maxLength={120}
              placeholder="e.g. Vegetable biryani"
              value={formData.foodName}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              required
              rows={3}
              maxLength={500}
              placeholder="What it is, how it is packed, allergens, when it was prepared"
              value={formData.description}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="foodType">Food Category</label>
              <select
                id="foodType"
                name="foodType"
                value={formData.foodType}
                onChange={handleInputChange}
              >
                <option value="Prepared Meals">Cooked / Prepared Meals</option>
                <option value="Bakery & Bread">Bakery & Bread</option>
                <option value="Fresh Produce">Fresh Produce / Fruits</option>
                <option value="Dairy & Chilled">Dairy & Chilled Items</option>
                <option value="Packaged Goods">Packaged / Dry Goods</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="servings">Estimated Servings</label>
              <input
                id="servings"
                name="servings"
                type="number"
                required
                min="1"
                max="100000"
                step="1"
                placeholder="e.g. 50"
                value={formData.servings}
                onChange={handleInputChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="location">Pickup Location</label>
            <input
              id="location"
              name="location"
              type="text"
              required
              maxLength={200}
              placeholder="Street address or landmark"
              value={formData.location}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="pickupWindow">Pickup Window</label>
              <select
                id="pickupWindow"
                name="pickupWindow"
                value={formData.pickupWindow}
                onChange={handleInputChange}
              >
                <option value="Within 1 hour">Immediate (Next 1 hour)</option>
                <option value="Within 2 hours">Within 2 hours</option>
                <option value="This afternoon">This afternoon (until 5 PM)</option>
                <option value="Tonight before 10pm">Tonight before 10 PM</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="contact">Phone or Email</label>
              <input
                id="contact"
                name="contact"
                type="text"
                required
                maxLength={120}
                placeholder="For pickup coordination"
                value={formData.contact}
                onChange={handleInputChange}
              />
              <span className="form-hint">Shared only with the NGO that claims this donation.</span>
            </div>
          </div>

          <div className="notice-box">
            <AlertCircle size={16} />
            <span>Protected under the Bill Emerson Good Samaritan Food Donation Act.</span>
          </div>

          {error && (
            <div className="form-error" role="alert">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={status === 'submitting'}>
              <HeartHandshake size={18} />
              <span>{status === 'submitting' ? 'Publishing…' : 'Publish Donation Alert'}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function FindView() {
  const [loadState, setLoadState] = useState('loading'); // loading | ready | error
  const [loadError, setLoadError] = useState('');
  const [donations, setDonations] = useState([]);
  const [ngoName, setNgoName] = useState('');
  const [claimingId, setClaimingId] = useState(null);
  const [claimErrors, setClaimErrors] = useState({}); // id -> message
  const [claimed, setClaimed] = useState({}); // id -> claim response

  const load = useCallback(async () => {
    setLoadState('loading');
    setLoadError('');
    try {
      setDonations(await listDonations({ status: 'available' }));
      setLoadState('ready');
    } catch (err) {
      setLoadError(err.message);
      setLoadState('error');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleClaim = async (donation) => {
    const name = ngoName.trim();
    if (!name) {
      setClaimErrors((prev) => ({ ...prev, [donation.id]: 'Enter your organization name above before claiming.' }));
      return;
    }
    setClaimErrors((prev) => ({ ...prev, [donation.id]: '' }));
    setClaimingId(donation.id);
    try {
      const result = await claimDonation(donation.id, name);
      setClaimed((prev) => ({ ...prev, [donation.id]: result }));
    } catch (err) {
      setClaimErrors((prev) => ({ ...prev, [donation.id]: err.message }));
      // Someone else may have claimed it, or it expired: refresh what is shown,
      // but keep any donations this user already claimed visible.
      if (err.status === 409) {
        try {
          const fresh = await listDonations({ status: 'available' });
          setDonations((prev) => {
            const keep = prev.filter((d) => claimed[d.id]);
            const freshIds = new Set(fresh.map((d) => d.id));
            return [...fresh, ...keep.filter((d) => !freshIds.has(d.id))];
          });
        } catch {
          /* keep the current list; the claim error is already shown */
        }
      }
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <div className="modal-body">
      <div className="modal-header">
        <div className="modal-icon-wrap find">
          <Search size={24} />
        </div>
        <div>
          <h3 id="modal-title" className="modal-title">Find Surplus Food</h3>
          <p className="modal-subtitle">Available donations listed by donors on FoodBridge</p>
        </div>
      </div>

      <div className="feed-filter-bar">
        <span className="live-pulse-badge">
          <span className="pulse-dot"></span> Live Listings
        </span>
        <button
          type="button"
          className="btn btn-secondary refresh-btn"
          onClick={load}
          disabled={loadState === 'loading'}
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="form-group ngo-name-field">
        <label htmlFor="ngoName">Your Organization Name</label>
        <input
          id="ngoName"
          type="text"
          maxLength={120}
          placeholder="e.g. Community Kitchen Trust"
          value={ngoName}
          onChange={(e) => setNgoName(e.target.value)}
        />
        <span className="form-hint">Required to claim. Organizations are not verified in this version.</span>
      </div>

      {loadState === 'loading' && (
        <div className="feed-state" role="status">Loading available donations…</div>
      )}

      {loadState === 'error' && (
        <div className="feed-state feed-state-error" role="alert">
          <AlertCircle size={18} />
          <p>{loadError}</p>
          <button type="button" className="btn btn-secondary" onClick={load}>Try again</button>
        </div>
      )}

      {loadState === 'ready' && donations.length === 0 && (
        <div className="feed-state">
          <p><strong>No donations are available right now.</strong></p>
          <p>New listings appear here as soon as donors post them. Try refreshing in a little while.</p>
        </div>
      )}

      {loadState === 'ready' && donations.length > 0 && (
        <div className="surplus-list">
          {donations.map((item) => {
            const result = claimed[item.id];
            return (
              <div key={item.id} className="feed-item">
                <div className="feed-item-top">
                  <div>
                    <h4 className="feed-source">{item.food_name}</h4>
                    <p className="feed-category">
                      {item.donor_name}{item.category ? ` · ${item.category}` : ''}
                    </p>
                  </div>
                  <span className="feed-status-badge">{result ? 'Claimed by you' : 'Available'}</span>
                </div>

                <p className="feed-desc">{item.description}</p>

                <div className="feed-item-meta">
                  <span className="feed-meta-pill">
                    <MapPin size={13} />
                    {item.location}
                  </span>
                  <span className="feed-meta-pill">
                    <Clock size={13} />
                    Pickup by {formatDeadline(item.pickup_deadline)}
                  </span>
                  <span className="feed-meta-pill highlight">
                    {item.servings} servings
                  </span>
                </div>

                {result ? (
                  <div className="claim-success" role="status">
                    <CheckCircle2 size={18} />
                    <div>
                      <strong>Reserved for {result.claimed_by}.</strong>
                      <p>
                        Contact the donor to arrange pickup: <strong>{result.donor_contact}</strong>
                      </p>
                      <p className="form-hint">Save this contact now. It is not shown again after you close this window.</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className="btn btn-primary claim-btn"
                      disabled={claimingId !== null}
                      onClick={() => handleClaim(item)}
                    >
                      {claimingId === item.id ? 'Claiming…' : 'Claim Donation For Pickup'}
                    </button>
                    {claimErrors[item.id] && (
                      <div className="form-error" role="alert">
                        <AlertCircle size={16} />
                        <span>{claimErrors[item.id]}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="modal-footer-note">
        <Sparkles size={14} />
        <span>Are you a newly registered NGO? Complete your verification to unlock scheduled daily routes.</span>
      </div>
    </div>
  );
}

export default function ActionModal({ isOpen, mode, onClose }) {
  // This component has no hooks, so returning early here is safe. The views
  // below own their state and are unmounted (and reset) whenever the modal closes.
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-container"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>

        {mode === 'donate' ? <DonateView onClose={onClose} /> : <FindView />}
      </div>
    </div>
  );
}
