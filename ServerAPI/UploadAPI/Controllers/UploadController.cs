using Azure.Storage.Blobs;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;

namespace UploadAPI.Controllers
{
    [Route("api/")]
    [ApiController]
    public class UploadController : ControllerBase
    {
        private readonly BlobServiceClient _blobServiceClient;
        private readonly string _containerName;

        public UploadController(IConfiguration configuration)
        {
            var connectionString = configuration.GetValue<string>("AzureBlobStorage:ConnectionString");
            _containerName = configuration.GetValue<string>("AzureBlobStorage:ContainerName");
            _blobServiceClient = new BlobServiceClient(connectionString);
        }

        [HttpPost("upload")]
        public async Task<IActionResult> UploadFiles(List<IFormFile> files)
        {
            if (files == null || files.Count == 0)
            {
                return BadRequest("No files received from the upload");
            }
            var containerClient = _blobServiceClient.GetBlobContainerClient(_containerName);
            await containerClient.CreateIfNotExistsAsync();

            foreach (var file in files)
            {
                if (file.Length > 0)
                {
                    var newFileName = $"{Path.GetFileNameWithoutExtension(file.FileName)}_{DateTime.UtcNow:yyyyMMddHHmmss}{Path.GetExtension(file.FileName)}";
                    var blobClient = containerClient.GetBlobClient(newFileName);

                    using (var stream = file.OpenReadStream())
                    {
                        await blobClient.UploadAsync(stream, true);
                    }

                    // print out details of file
                    Console.WriteLine($"File name: {newFileName}");
                    Console.WriteLine($"File size: {file.Length}");
                    Console.WriteLine($"Content type: {file.ContentType}");
                }
            }

            return Ok("Files successfully uploaded");
        }
    }
}
