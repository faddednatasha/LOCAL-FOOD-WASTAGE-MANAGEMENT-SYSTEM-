-- ---------- FOOD PROVIDERS & RECEIVERS ----------

-- 1. How many food providers and receivers are there in each city?
SELECT
    city,
    COUNT(DISTINCT provider_id) AS provider_count,
    0 AS receiver_count
FROM providers
GROUP BY city;

-- 2. Which type of food provider contributes the most food (by total quantity listed)?
SELECT
    provider_type,
    SUM(quantity) AS total_quantity
FROM food_listings
GROUP BY provider_type
ORDER BY total_quantity DESC;

-- 3. What is the contact information of food providers in a specific city?
SELECT name, type, address, contact
FROM providers
WHERE city = :city;  

-- 4. Which receivers have claimed the most food (by quantity, completed claims only)?
SELECT
    r.receiver_id,
    r.name,
    SUM(f.quantity) AS total_quantity_claimed
FROM claims c
JOIN receivers r ON r.receiver_id = c.receiver_id
JOIN food_listings f ON f.food_id = c.food_id
WHERE LOWER(c.status) = 'completed'
GROUP BY r.receiver_id, r.name
ORDER BY total_quantity_claimed DESC
LIMIT 10;

-- ---------- FOOD LISTINGS & AVAILABILITY ----------

-- 5. What is the total quantity of food available from all providers?
SELECT SUM(quantity) AS total_quantity_available FROM food_listings;

-- 6. Which city has the highest number of food listings?
SELECT location AS city, COUNT(*) AS listing_count
FROM food_listings
GROUP BY location
ORDER BY listing_count DESC
LIMIT 10;

-- 7. What are the most commonly available food types?
SELECT food_type, COUNT(*) AS listing_count
FROM food_listings
GROUP BY food_type
ORDER BY listing_count DESC;

-- ---------- CLAIMS & DISTRIBUTION ----------

-- 8. How many food claims have been made for each food item?
SELECT
    f.food_id,
    f.food_name,
    COUNT(c.claim_id) AS claim_count
FROM food_listings f
LEFT JOIN claims c ON c.food_id = f.food_id
GROUP BY f.food_id, f.food_name
ORDER BY claim_count DESC
LIMIT 15;

-- 9. Which provider has had the highest number of successful (completed) food claims?
SELECT
    p.provider_id,
    p.name,
    COUNT(c.claim_id) AS completed_claims
FROM claims c
JOIN food_listings f ON f.food_id = c.food_id
JOIN providers p ON p.provider_id = f.provider_id
WHERE LOWER(c.status) = 'completed'
GROUP BY p.provider_id, p.name
ORDER BY completed_claims DESC
LIMIT 10;

-- 10. What percentage of food claims are completed vs. pending vs. cancelled?
SELECT
    status,
    COUNT(*) AS claim_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM claims
GROUP BY status;

-- ---------- ANALYSIS & INSIGHTS ----------

-- 11. What is the average quantity of food claimed per receiver (completed claims)?
SELECT
    ROUND(AVG(receiver_total), 2) AS avg_quantity_claimed_per_receiver
FROM (
    SELECT c.receiver_id, SUM(f.quantity) AS receiver_total
    FROM claims c
    JOIN food_listings f ON f.food_id = c.food_id
    WHERE LOWER(c.status) = 'completed'
    GROUP BY c.receiver_id
) per_receiver;

-- 12. Which meal type is claimed the most?
SELECT
    f.meal_type,
    COUNT(c.claim_id) AS claim_count
FROM claims c
JOIN food_listings f ON f.food_id = c.food_id
GROUP BY f.meal_type
ORDER BY claim_count DESC;

-- 13. What is the total quantity of food donated by each provider?
SELECT
    p.provider_id,
    p.name,
    SUM(f.quantity) AS total_donated
FROM food_listings f
JOIN providers p ON p.provider_id = f.provider_id
GROUP BY p.provider_id, p.name
ORDER BY total_donated DESC
LIMIT 15;

-- 14. Which unclaimed food items expire soonest? (highest risk of being wasted)
SELECT
    f.food_id,
    f.food_name,
    f.quantity,
    f.expiry_date,
    f.location,
    p.name AS provider_name
FROM food_listings f
JOIN providers p ON p.provider_id = f.provider_id
WHERE f.food_id NOT IN (
      SELECT food_id FROM claims WHERE LOWER(status) = 'completed'
  )
ORDER BY f.expiry_date ASC
LIMIT 20;

-- 15. Monthly trend of claims
SELECT
    strftime('%Y-%m', timestamp) AS month,
    COUNT(*) AS claim_count
FROM claims
GROUP BY month
ORDER BY month;