// MongoDB initialization script — runs once on first container start
// Creates all required collections and indexes for ghana-tax-system

db = db.getSiblingDB("ghana_tax_db");

// ─── traders ──────────────────────────────────────────────────────────────────
db.createCollection("traders");
db.traders.createIndex({ tin_number: 1 }, { unique: true, name: "tin_unique" });
db.traders.createIndex({ phone_number: 1 }, { name: "phone_idx" });
db.traders.createIndex({ created_at: -1 }, { name: "created_at_desc" });
db.traders.createIndex({ channel: 1 }, { name: "channel_idx" });

// ─── businesses ───────────────────────────────────────────────────────────────
db.createCollection("businesses");
db.businesses.createIndex({ owner_trader_id: 1 }, { name: "owner_idx" });

// ─── locations ────────────────────────────────────────────────────────────────
db.createCollection("locations");
db.locations.createIndex({ region: 1 }, { name: "region_idx" });
db.locations.createIndex({ district: 1 }, { name: "district_idx" });

// ─── admins ───────────────────────────────────────────────────────────────────
db.createCollection("admins");
db.admins.createIndex({ email: 1 }, { unique: true, name: "email_unique" });

// ─── audit_logs ───────────────────────────────────────────────────────────────
db.createCollection("audit_logs");
db.audit_logs.createIndex({ created_at: -1 }, { name: "created_at_desc" });
db.audit_logs.createIndex({ actor_id: 1 }, { name: "actor_idx" });
db.audit_logs.createIndex({ action: 1 }, { name: "action_idx" });
db.audit_logs.createIndex({ entity_type: 1 }, { name: "entity_type_idx" });

// ─── ussd_sessions ────────────────────────────────────────────────────────────
db.createCollection("ussd_sessions");
db.ussd_sessions.createIndex({ session_id: 1 }, { unique: true, name: "session_unique" });
// TTL index: auto-delete sessions after 30 minutes of inactivity
db.ussd_sessions.createIndex(
  { last_activity_at: 1 },
  { expireAfterSeconds: 1800, name: "session_ttl" }
);

print("ghana_tax_db: all collections and indexes created successfully.");
