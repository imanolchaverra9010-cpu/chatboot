-- Script para crear las tablas de los nuevos módulos (MySQL)
-- Ejecutar en: u659323332_ebano_company
-- Uso: mysql -u usuario -p u659323332_ebano_company < crear_tablas_modulos.sql

-- 1. Tabla alertas
CREATE TABLE IF NOT EXISTS `alertas` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `titulo` varchar(255) NOT NULL,
    `mensaje` longtext NOT NULL,
    `tipo` varchar(20) NOT NULL DEFAULT 'general',
    `fecha_inicio` datetime(6) NOT NULL,
    `fecha_fin` datetime(6) DEFAULT NULL,
    `activo` tinyint(1) NOT NULL DEFAULT 1,
    `prioridad` int NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Tabla eventos_deportivos (si no existe)
CREATE TABLE IF NOT EXISTS `eventos_deportivos` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `nombre` varchar(255) NOT NULL,
    `tipo_evento` varchar(50) NOT NULL DEFAULT 'futbol',
    `descripcion` longtext,
    `equipo_local` varchar(100) DEFAULT NULL,
    `equipo_visitante` varchar(100) DEFAULT NULL,
    `fecha_evento` datetime(6) NOT NULL,
    `fecha_fin` datetime(6) DEFAULT NULL,
    `lugar` varchar(255) NOT NULL,
    `direccion` longtext,
    `barrio` varchar(100) DEFAULT NULL,
    `precio_entrada` decimal(10,2) DEFAULT NULL,
    `entrada_gratis` tinyint(1) NOT NULL DEFAULT 0,
    `organizador` varchar(200) DEFAULT NULL,
    `contacto` varchar(20) DEFAULT NULL,
    `imagen` varchar(200) DEFAULT NULL,
    `activo` tinyint(1) NOT NULL DEFAULT 1,
    `destacado` tinyint(1) NOT NULL DEFAULT 0,
    `fecha_creacion` datetime(6) NOT NULL,
    `fecha_actualizacion` datetime(6) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Tabla tramites_requisitos
CREATE TABLE IF NOT EXISTS `tramites_requisitos` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `nombre` varchar(255) NOT NULL,
    `descripcion` longtext NOT NULL,
    `entidad` varchar(200) DEFAULT NULL,
    `requisitos` json DEFAULT NULL,
    `documentos_necesarios` longtext,
    `costo` decimal(10,2) DEFAULT NULL,
    `link_turno` varchar(200) DEFAULT NULL,
    `link_info` varchar(200) DEFAULT NULL,
    `horario_atencion` longtext,
    `activo` tinyint(1) NOT NULL DEFAULT 1,
    `orden` int NOT NULL DEFAULT 0,
    `fecha_creacion` datetime(6) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Tabla turnos (FK a chatbot_conversation)
CREATE TABLE IF NOT EXISTS `turnos` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `servicio` varchar(200) NOT NULL,
    `fecha_turno` date NOT NULL,
    `hora_inicio` time(6) NOT NULL,
    `hora_fin` time(6) NOT NULL,
    `telefono_reserva` varchar(20) DEFAULT NULL,
    `conversation_id` bigint DEFAULT NULL,
    `estado` varchar(20) NOT NULL DEFAULT 'disponible',
    `notas` longtext,
    `fecha_creacion` datetime(6) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `turnos_conversation_id_fk` (`conversation_id`),
    CONSTRAINT `turnos_conversation_id_fk` FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversation` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Tabla escalamientos
CREATE TABLE IF NOT EXISTS `escalamientos` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `conversation_id` bigint NOT NULL,
    `motivo` longtext NOT NULL,
    `canal_destino` varchar(50) NOT NULL DEFAULT 'whatsapp',
    `numero_whatsapp` varchar(20) DEFAULT NULL,
    `ticket_crm` varchar(100) DEFAULT NULL,
    `estado` varchar(20) NOT NULL DEFAULT 'pendiente',
    `feedback_sistema` longtext,
    `resuelto_por_bot` tinyint(1) DEFAULT NULL,
    `fecha_escalamiento` datetime(6) NOT NULL,
    `fecha_resolucion` datetime(6) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `escalamientos_conversation_id_fk` (`conversation_id`),
    CONSTRAINT `escalamientos_conversation_id_fk` FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversation` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Tabla consultas_analiticas
CREATE TABLE IF NOT EXISTS `consultas_analiticas` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `phone_number` varchar(20) NOT NULL,
    `motivo_consulta` varchar(200) DEFAULT NULL,
    `intent_detectado` varchar(100) DEFAULT NULL,
    `barrio` varchar(100) DEFAULT NULL,
    `edad_rango` varchar(20) DEFAULT NULL,
    `resuelto` tinyint(1) NOT NULL DEFAULT 0,
    `escalado_humano` tinyint(1) NOT NULL DEFAULT 0,
    `feedback` longtext,
    `metadata` json DEFAULT NULL,
    `fecha_consulta` datetime(6) NOT NULL,
    `conversation_id` bigint DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `consultas_analiticas_phone_number_idx` (`phone_number`),
    KEY `consultas_analiticas_conversation_id_fk` (`conversation_id`),
    CONSTRAINT `consultas_analiticas_conversation_id_fk` FOREIGN KEY (`conversation_id`) REFERENCES `chatbot_conversation` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Tabla boleteria (FK a eventos_deportivos)
CREATE TABLE IF NOT EXISTS `boleteria` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `nombre_evento` varchar(255) DEFAULT NULL,
    `precio_general` decimal(10,2) DEFAULT NULL,
    `precio_vip` decimal(10,2) DEFAULT NULL,
    `precio_niños` decimal(10,2) DEFAULT NULL,
    `entrada_gratis` tinyint(1) NOT NULL DEFAULT 0,
    `link_compra` varchar(200) DEFAULT NULL,
    `puntos_venta` longtext,
    `notas` longtext,
    `activo` tinyint(1) NOT NULL DEFAULT 1,
    `fecha_creacion` datetime(6) NOT NULL,
    `evento_id` bigint DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `boleteria_evento_id_fk` (`evento_id`),
    CONSTRAINT `boleteria_evento_id_fk` FOREIGN KEY (`evento_id`) REFERENCES `eventos_deportivos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
