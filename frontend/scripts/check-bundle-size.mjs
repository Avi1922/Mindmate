import { gzipSync } from 'node:zlib'
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const assetsDirectory = fileURLToPath(new URL('../dist/assets/', import.meta.url))
const maximumGzipBytes = 250 * 1024
const files = await readdir(assetsDirectory)
const oversized = []

for (const file of files.filter((name) => name.endsWith('.js'))) {
  const contents = await readFile(join(assetsDirectory, file))
  const gzipBytes = gzipSync(contents).byteLength
  console.log(`${file}: ${(gzipBytes / 1024).toFixed(1)} KiB gzip`)
  if (gzipBytes > maximumGzipBytes) oversized.push(file)
}

if (oversized.length) {
  throw new Error(`JavaScript bundle budget exceeded: ${oversized.join(', ')}`)
}
