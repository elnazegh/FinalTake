-- Run once against an existing FinalTake database after backing it up.
-- Intentionally keep media_id as text until the separate media catalog
-- database changes are integrated. User ownership remains a real FK.
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    media_id VARCHAR(64) NOT NULL,
    rating DECIMAL(2,1) NOT NULL,
    review_text TEXT NOT NULL,
    tags_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reviews_media_id (media_id),
    INDEX idx_reviews_user_id (user_id),
    CONSTRAINT fk_reviews_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);
