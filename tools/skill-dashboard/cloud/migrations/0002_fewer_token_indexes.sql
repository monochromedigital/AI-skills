-- Every index adds one written row per insert, and D1's free plan allows
-- 100,000 written rows a day. Nothing reads token_usage by time, session or
-- model yet, so those three indexes only cost writes. Kept: by project and
-- by machine, the two ways the console will slice cost first.
DROP INDEX IF EXISTS token_usage_ts;
DROP INDEX IF EXISTS token_usage_session;
DROP INDEX IF EXISTS token_usage_model;
