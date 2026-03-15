-- 1. Crear la base de datos IrriGo si no existe
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'IrriGo')
BEGIN
    CREATE DATABASE IrriGo;
END
GO

-- Usar la base de datos
USE IrriGo;
GO

-- 2. CREACIÓN DE TABLAS

-- Tabla Usuario
CREATE TABLE Usuario (
    IDusuario INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Apellido VARCHAR(100),
    Email VARCHAR(150) UNIQUE NOT NULL,
    Contraseña VARCHAR(255) NOT NULL,
    Teléfono VARCHAR(20)
);

-- Tabla Predio
CREATE TABLE Predio (
    IDpredio INT IDENTITY(1,1) PRIMARY KEY,
    NombrePredio VARCHAR(100) NOT NULL,
    Ubicación VARCHAR(255),
    FechaCreación DATETIME DEFAULT GETDATE()
);

-- Tabla Usuario_predio (Tabla intermedia para Roles específicos por Predio)
CREATE TABLE Usuario_predio (
    IDusuario INT,
    IDpredio INT,
    Rol VARCHAR(50) NOT NULL,
    Fecha_Asignacion DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (IDusuario, IDpredio),
    FOREIGN KEY (IDusuario) REFERENCES Usuario(IDusuario),
    FOREIGN KEY (IDpredio) REFERENCES Predio(IDpredio)
);

-- Tabla RegistroAuditoria
CREATE TABLE RegistroAuditoria (
    IDregistro INT IDENTITY(1,1) PRIMARY KEY,
    IDusuario INT,
    ID_Area INT,
    Fecha_Modificacion DATETIME DEFAULT GETDATE(),
    Dato_Modificado VARCHAR(MAX),
    FOREIGN KEY (IDusuario) REFERENCES Usuario(IDusuario)
);

-- Tabla ModuloControl
CREATE TABLE ModuloControl (
    ID_Modulo INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(100),
    IdentificadorRed VARCHAR(100),
    Estado BIT DEFAULT 1,
    UltimaConexion DATETIME,
    Ultima_Actualizacion DATETIME
);

-- Tabla AreaRiego
CREATE TABLE AreaRiego (
    ID_Area INT IDENTITY(1,1) PRIMARY KEY,
    IDpredio INT,
    ID_Modulo INT,
    Nombre VARCHAR(100),
    Num_Hectareas FLOAT,
    Estado BIT DEFAULT 1,
    FOREIGN KEY (IDpredio) REFERENCES Predio(IDpredio),
    FOREIGN KEY (ID_Modulo) REFERENCES ModuloControl(ID_Modulo)
);

-- Tabla Sensor 
CREATE TABLE Sensor (
    IDsensor INT IDENTITY(1,1) PRIMARY KEY,
    ID_Modulo INT,
    ID_Area INT,
    Bateria FLOAT,
    Señal FLOAT,
    FOREIGN KEY (ID_Modulo) REFERENCES ModuloControl(ID_Modulo),
    FOREIGN KEY (ID_Area) REFERENCES AreaRiego(ID_Area)
);

-- Tabla ConfiguracionCultivo
CREATE TABLE ConfiguracionCultivo (
    ID_Configuracion INT IDENTITY(1,1) PRIMARY KEY,
    ID_Area INT UNIQUE, 
    TipoCultivo VARCHAR(100),
    TipoTierra VARCHAR(100),
    CapacidadCampo FLOAT,
    PuntoMarchitez FLOAT,
    RangoHumedadMIN FLOAT,
    RangoHumedadMAX FLOAT,
    LaminaRiego FLOAT,
    DesarrolloVegetativo FLOAT,
    FOREIGN KEY (ID_Area) REFERENCES AreaRiego(ID_Area)
);

-- Tabla Alerta
CREATE TABLE Alerta (
    ID_Alerta INT IDENTITY(1,1) PRIMARY KEY,
    ID_area INT,
    IDusuario INT,
    Fecha DATETIME DEFAULT GETDATE(),
    Tipo VARCHAR(100),
    Severidad VARCHAR(50),
    Estado BIT DEFAULT 0,
    Leida BIT DEFAULT 0,
    FOREIGN KEY (ID_area) REFERENCES AreaRiego(ID_Area),
    FOREIGN KEY (IDusuario) REFERENCES Usuario(IDusuario)
);

-- Tabla MedicionHistorica
CREATE TABLE MedicionHistorica (
    ID_Medicion INT IDENTITY(1,1) PRIMARY KEY,
    ID_Area INT,
    Fecha DATETIME DEFAULT GETDATE(),
    Temperatura_Suelo FLOAT,
    Humedad_suelo FLOAT,
    Evapotranspiracion FLOAT,
    Conductividad_suelo FLOAT, 
    consumo_agua FLOAT,
    Desarrollo_vegetativa FLOAT,
    FOREIGN KEY (ID_Area) REFERENCES AreaRiego(ID_Area)
);
GO
