async def watch_project_and_send_zip(self, project: str = "foo", ext: str = "drc"):
        """Continuously watches for new files and streams ZIP when detected."""
        bar_path = os.path.join(self.media_path, project, "bar")

        known_files = set(os.listdir(bar_path))  # Track existing files

        while True:
            current_files = set(os.listdir(bar_path))
            new_files = current_files - known_files

            
            print(current_files)


            if new_files:
                known_files = current_files  # Update known files

                # Create ZIP and send to clients
                zip_filename, zip_path = self.create_zip_stream(project, ext)

                print("-------zip filename: ", zip_filename)
                print("-------zip path: ", zip_path)

                if zip_filename:
                    async with aiofiles.open(zip_path, "rb") as f:
                        while chunk := await f.read(65536):  # Read in chunks
                            yield chunk
            await asyncio.sleep(2)  # Check every 2 seconds