package logger

import (
	"os"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

func New() *zap.SugaredLogger {
	// Консольный вывод (debug+)
	consoleEncoder := zapcore.NewConsoleEncoder(zap.NewDevelopmentEncoderConfig())
	consoleCore := zapcore.NewCore(consoleEncoder, zapcore.AddSync(os.Stdout), zapcore.DebugLevel)

	// Файловый вывод (info+)
	fileWriter := zapcore.AddSync(&lumberjack.Logger{
		Filename:   "./logs/meetping.log",
		MaxSize:    10, // megabytes
		MaxBackups: 3,
		MaxAge:     28,   // days
		Compress:   true, // gzip
	})
	fileEncoder := zapcore.NewConsoleEncoder(zap.NewProductionEncoderConfig())
	fileCore := zapcore.NewCore(fileEncoder, fileWriter, zapcore.InfoLevel)

	// Объединяем оба потока
	combinedCore := zapcore.NewTee(consoleCore, fileCore)

	logger := zap.New(combinedCore, zap.AddCaller())
	return logger.Sugar()
}

func InitLogger() *zap.SugaredLogger {
	writer := zapcore.AddSync(&lumberjack.Logger{
		Filename:   "logs/app.log",
		MaxSize:    10, // megabytes
		MaxBackups: 3,
		MaxAge:     14,   // days
		Compress:   true, // gzip
	})

	core := zapcore.NewCore(
		zapcore.NewConsoleEncoder(zap.NewDevelopmentEncoderConfig()),
		writer,
		zap.InfoLevel,
	)

	logger := zap.New(core).Sugar()
	return logger
}
