-- Script SQL para arreglar permisos de PostgreSQL en Digital Ocean
-- Ejecutar esto en la consola de PostgreSQL

-- Conectarse a la base de datos
\c defaultdb

-- Dar todos los permisos al schema public
GRANT ALL ON SCHEMA public TO doadmin;
GRANT ALL ON SCHEMA public TO PUBLIC;

-- Dar permisos por defecto para tablas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO doadmin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO PUBLIC;

-- Dar permisos por defecto para secuencias futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO doadmin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO PUBLIC;

-- Verificar permisos
\dp
