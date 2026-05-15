-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: tfg
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `activos`
--

DROP TABLE IF EXISTS `activos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `activos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `ticker` varchar(25) NOT NULL,
  `tipo` enum('accion','etf') NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activos`
--

LOCK TABLES `activos` WRITE;
/*!40000 ALTER TABLE `activos` DISABLE KEYS */;
/*!40000 ALTER TABLE `activos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `analisis`
--

DROP TABLE IF EXISTS `analisis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analisis` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `activo_id` int(11) NOT NULL,
  `precio_actual` decimal(12,2) NOT NULL,
  `valor_estimado` decimal(12,2) NOT NULL,
  `resultado` varchar(50) NOT NULL,
  `fecha` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `activo_id` (`activo_id`),
  CONSTRAINT `analisis_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `analisis_ibfk_2` FOREIGN KEY (`activo_id`) REFERENCES `activos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `analisis`
--

LOCK TABLES `analisis` WRITE;
/*!40000 ALTER TABLE `analisis` DISABLE KEYS */;
/*!40000 ALTER TABLE `analisis` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cartera_activos`
--

DROP TABLE IF EXISTS `cartera_activos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cartera_activos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cartera_id` int(11) NOT NULL,
  `activo_id` int(11) NOT NULL,
  `cantidad` decimal(12,2) NOT NULL,
  `precio_compra` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cartera_id` (`cartera_id`),
  KEY `activo_id` (`activo_id`),
  CONSTRAINT `cartera_activos_ibfk_1` FOREIGN KEY (`cartera_id`) REFERENCES `carteras` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cartera_activos_ibfk_2` FOREIGN KEY (`activo_id`) REFERENCES `activos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cartera_activos`
--

LOCK TABLES `cartera_activos` WRITE;
/*!40000 ALTER TABLE `cartera_activos` DISABLE KEYS */;
/*!40000 ALTER TABLE `cartera_activos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `carteras`
--

DROP TABLE IF EXISTS `carteras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `carteras` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `nombreCartera` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `carteras_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `carteras`
--

LOCK TABLES `carteras` WRITE;
/*!40000 ALTER TABLE `carteras` DISABLE KEYS */;
/*!40000 ALTER TABLE `carteras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientos`
--

DROP TABLE IF EXISTS `movimientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) NOT NULL,
  `tipo` enum('ingreso','gasto') NOT NULL,
  `concepto` varchar(50) DEFAULT NULL,
  `categoria` enum('fijo','ocio','ahorro_inversion') NOT NULL,
  `cantidad` decimal(12,2) NOT NULL,
  `fecha` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `movimientos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientos`
--

LOCK TABLES `movimientos` WRITE;
/*!40000 ALTER TABLE `movimientos` DISABLE KEYS */;
/*!40000 ALTER TABLE `movimientos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombreUsuario` varchar(190) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(500) DEFAULT NULL,
  `pct_fijo` int(11) DEFAULT 50,
  `pct_ocio` int(11) DEFAULT 30,
  `pct_ahorro` int(11) DEFAULT 20,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Guillermo','gui@test.com','scrypt:32768:8:1$wiuSc5eb7BpJvcaB$e569885e4e918885cf26ec931b707ca15cb85a36c40fba42a8514fe7a5e56d7a88a0eaf42a1eeada0ea61cd9310a7fa33083db4c240ed3430c768026daad7112',50,30,20),(2,'Guillermo','guillermo.e.r.2005@gmail.com','scrypt:32768:8:1$jV3HjbjYdkwis31M$399b82f777446119c5eb288a2e3f3c45463867c5a324743427853497002830ccd61f6a0634593ab98f762d2c3a0d76d08e3562683852ed98179a0a388f2df456',50,30,20),(3,'mii','miitest@gmail.com','scrypt:32768:8:1$mWuPKHEQfoEJ30KQ$e5ab5d807282a197b175a83a34b759e388148f1b34204d1e44ec161f6f1ee6dbdef7e9b8d342c8a8955619e588349fd6b82fca3ce96c1fe5cabf6bc365ab3542',50,30,20),(4,'prueb1','prueba1@gmail.com','scrypt:32768:8:1$QNDXcxcKKAXyAKJv$69ea15320c1c3784c4779bd0487737e6b02c028242954218b7e491ba9dd227a5156b2df1648a7bac147ef118806e99d27e25a4548953bc331ea807a8cc53a493',60,20,20),(5,'prueba2','prueba2@gmail.com','scrypt:32768:8:1$uWpm5SxFFsuEkLBU$84386382197557631e43ac08c726090e8cb125332bf7c7932868fbf2cddafd095de60c6f1027eb4431cb9d70d2e398f07c5cc519301f162c5cd0189333901981',50,30,20),(6,'prueba3','prueba3@gmail.com','scrypt:32768:8:1$ysbEYApI6OwGuMZA$fad630ef3b9caf947d0b886fd1d5c17e2acf6f5f4527f7e72f4318bbeacf219d0726cc08d136c9906dd91883946b2edf9f9d95f84b993471c62f8e522e74317f',50,30,20);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-10 20:33:59
