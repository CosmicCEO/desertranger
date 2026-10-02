-- Desert Ranger schema (milestone 1). Run by install.php; safe on MySQL 5.6+ / MariaDB 10+.
-- Statements are separated by a line containing only ";" -- install.php splits on that.
-- No JSON column type (older MySQL); JSON is stored in TEXT.

-- Milestone 2 will fill this table (username/password accounts). Created now so
-- players.user_id / games.created_by_user_id can point at it without a migration.
CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(40)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at    DATETIME     NOT NULL,
  UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
;
CREATE TABLE IF NOT EXISTS games (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code               CHAR(4)      NOT NULL,             -- room code, e.g. "KQWE"
  status             VARCHAR(10)  NOT NULL DEFAULT 'lobby', -- lobby | active | finished
  board_id           VARCHAR(40)  NOT NULL DEFAULT 'desert-ranger',
  host_player_id     INT UNSIGNED NULL,
  turn_number        INT UNSIGNED NOT NULL DEFAULT 0,   -- +1 per roll/choice; clients must echo it
  current_seat       TINYINT UNSIGNED NOT NULL DEFAULT 0,
  pending_json       TEXT NULL,                         -- optional choice waiting (swap / shortcut)
  winner_player_id   INT UNSIGNED NULL,
  last_action_key    VARCHAR(64)  NULL,                 -- idempotency key of the last accepted action
  created_by_user_id INT UNSIGNED NULL,                 -- milestone 2
  created_at         DATETIME     NOT NULL,
  updated_at         DATETIME     NOT NULL,
  UNIQUE KEY uq_games_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
;
CREATE TABLE IF NOT EXISTS players (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  game_id      INT UNSIGNED NOT NULL,
  user_id      INT UNSIGNED NULL,                       -- milestone 2: link a seat to an account
  seat         TINYINT UNSIGNED NOT NULL,               -- 0..7, join order = turn order
  display_name VARCHAR(24)  NOT NULL,
  vehicle      VARCHAR(20)  NOT NULL,                   -- e.g. "bronco-orange"
  token_hash   CHAR(64)     NOT NULL,                   -- sha256 of the secret seat token
  position     TINYINT UNSIGNED NOT NULL DEFAULT 0,
  skip_turns   TINYINT UNSIGNED NOT NULL DEFAULT 0,
  joined_at    DATETIME     NOT NULL,
  last_seen_at DATETIME     NOT NULL,
  UNIQUE KEY uq_players_seat (game_id, seat),
  UNIQUE KEY uq_players_vehicle (game_id, vehicle),
  UNIQUE KEY uq_players_token (token_hash),
  KEY ix_players_user (user_id),
  CONSTRAINT fk_players_game FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
;
CREATE TABLE IF NOT EXISTS events (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  game_id     INT UNSIGNED NOT NULL,
  turn_number INT UNSIGNED NOT NULL,
  type        VARCHAR(16)  NOT NULL,                    -- join | start | turn | skip ...
  message     VARCHAR(500) NOT NULL,                    -- the log line shown to players
  payload     TEXT NULL,                                -- JSON: animation steps etc.
  cue         VARCHAR(16)  NULL,                        -- cheer | aww
  play_at_ms  BIGINT NULL,                              -- server clock (ms since epoch) to play the cue
  created_at  DATETIME     NOT NULL,
  KEY ix_events_game (game_id, id),
  CONSTRAINT fk_events_game FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
;
