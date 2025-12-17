-- load.sql: Carga datos iniciales

-- A. Estados de Video
INSERT INTO video_status (name) VALUES ('PENDING') ON CONFLICT (name) DO NOTHING;
INSERT INTO video_status (name) VALUES ('PROCESSED') ON CONFLICT (name) DO NOTHING;
INSERT INTO video_status (name) VALUES ('ERROR') ON CONFLICT (name) DO NOTHING;

-- B. Estados de Inspección
-- Nota: En SQL insertamos directamente los IDs si queremos, o dejamos que el serial corra.
-- Aquí confiamos en el orden de inserción o definimos explícitamente los campos.

INSERT INTO inspection_status (name, severity, is_anomaly) 
VALUES ('NORMAL', 0, FALSE);

INSERT INTO inspection_status (name, severity, is_anomaly) 
VALUES ('INCIDENT', 5, TRUE);

-- C. Categorías de Comida
INSERT INTO food_category (name, min_threshold) VALUES ('bacon', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('jalapeno', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('ketchup', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('lettuce', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('mayo', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('onion', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('pepper', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('pickles', 55.0) ON CONFLICT (name) DO NOTHING;
INSERT INTO food_category (name, min_threshold) VALUES ('tomato', 45.0) ON CONFLICT (name) DO NOTHING;