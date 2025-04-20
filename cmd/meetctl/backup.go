package main

import (
	"archive/zip"
	"io"
	"log"
	"os"
	"path/filepath"
)

func CreateBackup(outputPath string) error {
	zipFile, err := os.Create(outputPath)
	if err != nil {
		return err
	}
	defer zipFile.Close()

	archive := zip.NewWriter(zipFile)
	defer archive.Close()

	folders := []string{"data", "logs"}

	for _, folder := range folders {
		_ = filepath.Walk(folder, func(path string, info os.FileInfo, err error) error {
			if err != nil || info.IsDir() {
				return nil
			}
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()

			header, err := zip.FileInfoHeader(info)
			if err != nil {
				return err
			}
			header.Name = path
			header.Method = zip.Deflate

			writer, err := archive.CreateHeader(header)
			if err != nil {
				return err
			}
			_, err = io.Copy(writer, file)
			return err
		})
	}
	log.Println("Backup created at", outputPath)
	return nil
}
