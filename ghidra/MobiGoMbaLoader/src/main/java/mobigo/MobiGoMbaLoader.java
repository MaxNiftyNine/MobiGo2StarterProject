/* ###
 * IP: GHIDRA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package mobigo;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import ghidra.app.util.MemoryBlockUtils;
import ghidra.app.util.bin.BinaryReader;
import ghidra.app.util.bin.ByteProvider;
import ghidra.app.util.opinion.AbstractProgramWrapperLoader;
import ghidra.app.util.opinion.LoadSpec;
import ghidra.program.database.mem.FileBytes;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSpace;
import ghidra.program.model.data.ArrayDataType;
import ghidra.program.model.data.ByteDataType;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.DataUtilities;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.data.StructureDataType;
import ghidra.program.model.data.UnsignedShortDataType;
import ghidra.program.model.listing.CommentType;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.SymbolTable;
import ghidra.util.exception.CancelledException;

/**
 * Loader for the bM_gbMQa application container shared by MobiGo GAM files
 * and MobiGo 2 MBA files.
 *
 * Addresses in the header and in this loader are 16-bit word addresses.
 */
public class MobiGoMbaLoader extends AbstractProgramWrapperLoader {

	private static final String LOADER_NAME = "MobiGo MBA/GAM application";
	private static final byte[] MAGIC = "bM_gbMQa".getBytes(StandardCharsets.US_ASCII);
	private static final int HEADER_SIZE = 0x1000;
	private static final int MENU_ART_OFFSET = 0xc0;
	private static final int MENU_ART_SIZE = 0xd00;
	private static final int LAUNCHER_FOOTER_OFFSET = 0xdc0;
	private static final long HEADER_WORDS = HEADER_SIZE / 2;
	private static final long ADDRESS_SPACE_WORDS = 0x400000L;

	private record Header(long fileWords, long field0c, long field10, long entry,
			long loadAddress, long field1c, long field20, long field24, long field28,
			int storedCrc, int calculatedCrc, String title) {

		long runtimeBase() {
			return loadAddress - HEADER_WORDS;
		}

		long runtimeEnd() {
			return runtimeBase() + fileWords - 1;
		}

		long entryFileOffset() {
			return (entry - runtimeBase()) * 2;
		}
	}

	private record NamedAddress(long address, String name) {}

	private static final NamedAddress[] DOCUMENTED_ADDRESSES = {
		// PPU layers and global video control.
		new NamedAddress(0x7000, "PPU_L2_X_SCROLL"),
		new NamedAddress(0x7001, "PPU_L2_Y_SCROLL"),
		new NamedAddress(0x7004, "PPU_L2_ATTRIBUTES"),
		new NamedAddress(0x7005, "PPU_L2_CONTROL"),
		new NamedAddress(0x7006, "PPU_L2_TILEMAP"),
		new NamedAddress(0x7007, "PPU_L2_ATTRIBUTE_MAP"),
		new NamedAddress(0x7008, "PPU_L3_X_SCROLL"),
		new NamedAddress(0x7009, "PPU_L3_Y_SCROLL"),
		new NamedAddress(0x700c, "PPU_L3_ATTRIBUTES"),
		new NamedAddress(0x700d, "PPU_L3_CONTROL"),
		new NamedAddress(0x700e, "PPU_L3_TILEMAP"),
		new NamedAddress(0x700f, "PPU_L3_ATTRIBUTE_MAP"),
		new NamedAddress(0x7010, "PPU_L0_X_SCROLL"),
		new NamedAddress(0x7011, "PPU_L0_Y_SCROLL"),
		new NamedAddress(0x7012, "PPU_L0_ATTRIBUTES"),
		new NamedAddress(0x7013, "PPU_L0_CONTROL"),
		new NamedAddress(0x7014, "PPU_L0_TILEMAP"),
		new NamedAddress(0x7015, "PPU_L0_ATTRIBUTE_MAP"),
		new NamedAddress(0x7016, "PPU_L1_X_SCROLL"),
		new NamedAddress(0x7017, "PPU_L1_Y_SCROLL"),
		new NamedAddress(0x7018, "PPU_L1_ATTRIBUTES"),
		new NamedAddress(0x7019, "PPU_L1_CONTROL"),
		new NamedAddress(0x701a, "PPU_L1_TILEMAP"),
		new NamedAddress(0x701b, "PPU_L1_ATTRIBUTE_MAP"),
		new NamedAddress(0x7020, "PPU_L0_GFX_LOW"),
		new NamedAddress(0x7021, "PPU_L1_GFX_LOW"),
		new NamedAddress(0x7022, "PPU_SPRITE_GFX_LOW"),
		new NamedAddress(0x7023, "PPU_L2_GFX_LOW"),
		new NamedAddress(0x7024, "PPU_L3_GFX_LOW"),
		new NamedAddress(0x702b, "PPU_L0_GFX_HIGH"),
		new NamedAddress(0x702c, "PPU_L1_GFX_HIGH"),
		new NamedAddress(0x702d, "PPU_SPRITE_GFX_HIGH"),
		new NamedAddress(0x702e, "PPU_L2_GFX_HIGH"),
		new NamedAddress(0x702f, "PPU_L3_GFX_HIGH"),
		new NamedAddress(0x7038, "TFT_SCANLINE"),
		new NamedAddress(0x703a, "PALETTE_CTRL"),
		new NamedAddress(0x703c, "TV_SATURATION"),
		new NamedAddress(0x7042, "SPRITE_CTRL"),
		new NamedAddress(0x7050, "TFT_CTRL"),
		new NamedAddress(0x7051, "TFT_V_WIDTH"),
		new NamedAddress(0x7054, "TFT_FRAME_EDGE_LINE"),
		new NamedAddress(0x7055, "TFT_H_WIDTH"),
		new NamedAddress(0x705a, "TFT_STATUS"),
		new NamedAddress(0x7062, "VIDEO_IRQ_ENABLE"),
		new NamedAddress(0x7063, "VIDEO_IRQ_STATUS"),
		new NamedAddress(0x7070, "VIDEO_DMA_SOURCE"),
		new NamedAddress(0x7071, "VIDEO_DMA_DEST"),
		new NamedAddress(0x7072, "VIDEO_DMA_SIZE_GO"),
		new NamedAddress(0x7078, "FBI_LOW"),
		new NamedAddress(0x7079, "FBI_HIGH"),
		new NamedAddress(0x707a, "FBO_LOW"),
		new NamedAddress(0x707b, "FBO_HIGH"),
		new NamedAddress(0x707c, "FB_PPU_GO"),
		new NamedAddress(0x707e, "PPU_RAM_BANK"),
		new NamedAddress(0x707f, "PPU_ENABLE"),
		new NamedAddress(0x70e0, "RANDOM_STATUS"),
		new NamedAddress(0x7100, "ROW_SCROLL_RAM"),
		new NamedAddress(0x7200, "ROW_ZOOM_RAM"),
		new NamedAddress(0x7300, "PALETTE_WINDOW"),
		new NamedAddress(0x7400, "SPRITE_RAM"),

		// System, memory controller, NAND, and GPIO.
		new NamedAddress(0x7800, "BODY_ID"),
		new NamedAddress(0x7806, "RESET_CAUSE"),
		new NamedAddress(0x7807, "SYSTEM_CLOCK_CTRL"),
		new NamedAddress(0x780a, "WATCHDOG_CTRL"),
		new NamedAddress(0x780b, "WATCHDOG_CLEAR"),
		new NamedAddress(0x780e, "SLEEP_KEY"),
		new NamedAddress(0x780f, "POWER_STATE"),
		new NamedAddress(0x7810, "CS_BANK_CTRL"),
		new NamedAddress(0x7817, "PLL_MULTIPLIER"),
		new NamedAddress(0x7819, "CACHE_CTRL"),
		new NamedAddress(0x7820, "MCS0_CTRL"),
		new NamedAddress(0x7821, "MCS1_CTRL"),
		new NamedAddress(0x7822, "MCS2_CTRL"),
		new NamedAddress(0x7823, "MCS3_CTRL"),
		new NamedAddress(0x7824, "MCS4_CTRL"),
		new NamedAddress(0x784e, "NAND_ECC_RESULT0"),
		new NamedAddress(0x784f, "NAND_ECC_RESULT1"),
		new NamedAddress(0x7850, "NAND_CTRL"),
		new NamedAddress(0x7851, "NAND_COMMAND"),
		new NamedAddress(0x7852, "NAND_ADDRESS_LOW"),
		new NamedAddress(0x7853, "NAND_ADDRESS_HIGH"),
		new NamedAddress(0x7854, "NAND_DATA"),
		new NamedAddress(0x7855, "NAND_DMA_IRQ_CTRL"),
		new NamedAddress(0x7856, "NAND_TYPE"),
		new NamedAddress(0x785e, "NAND_ECC_RESULT2"),
		new NamedAddress(0x785f, "NAND_ECC_RESULT3"),
		new NamedAddress(0x7860, "GPIO_A_DATA"),
		new NamedAddress(0x7861, "GPIO_A_BUFFER"),
		new NamedAddress(0x7862, "GPIO_A_DIRECTION"),
		new NamedAddress(0x7863, "GPIO_A_ATTRIBUTE"),
		new NamedAddress(0x7868, "GPIO_B_DATA"),
		new NamedAddress(0x7869, "GPIO_B_BUFFER"),
		new NamedAddress(0x786a, "GPIO_B_DIRECTION"),
		new NamedAddress(0x786b, "GPIO_B_ATTRIBUTE"),
		new NamedAddress(0x7870, "GPIO_C_DATA"),
		new NamedAddress(0x7871, "GPIO_C_BUFFER"),
		new NamedAddress(0x7872, "GPIO_C_DIRECTION"),
		new NamedAddress(0x7873, "GPIO_C_ATTRIBUTE"),
		new NamedAddress(0x7878, "GPIO_D_DATA"),
		new NamedAddress(0x7879, "GPIO_D_BUFFER"),
		new NamedAddress(0x787a, "GPIO_D_DIRECTION"),
		new NamedAddress(0x787b, "GPIO_D_ATTRIBUTE"),
		new NamedAddress(0x7880, "GPIO_E_DATA"),
		new NamedAddress(0x7881, "GPIO_E_BUFFER"),
		new NamedAddress(0x7882, "GPIO_E_DIRECTION"),
		new NamedAddress(0x7883, "GPIO_E_ATTRIBUTE"),

		// Interrupts, timers, audio, RTC, SPI, and ADC.
		new NamedAddress(0x78a0, "INT_STATUS1"),
		new NamedAddress(0x78a1, "INT_STATUS2"),
		new NamedAddress(0x78a2, "INT_CTRL1"),
		new NamedAddress(0x78a3, "INT_CTRL2"),
		new NamedAddress(0x78a4, "INT_PRIORITY1"),
		new NamedAddress(0x78a5, "INT_PRIORITY2"),
		new NamedAddress(0x78b0, "TIMEBASE_A"),
		new NamedAddress(0x78b1, "TIMEBASE_B"),
		new NamedAddress(0x78b2, "TIMEBASE_C"),
		new NamedAddress(0x78c0, "TIMER_A_CTRL"),
		new NamedAddress(0x78c2, "TIMER_A_PRELOAD"),
		new NamedAddress(0x78c4, "TIMER_A_COUNT"),
		new NamedAddress(0x78c8, "TIMER_B_CTRL"),
		new NamedAddress(0x78ca, "TIMER_B_PRELOAD"),
		new NamedAddress(0x78cc, "TIMER_B_COUNT"),
		new NamedAddress(0x78d0, "TIMER_C_CTRL"),
		new NamedAddress(0x78d2, "TIMER_C_PRELOAD"),
		new NamedAddress(0x78d4, "TIMER_C_COUNT"),
		new NamedAddress(0x78d8, "TIMER_D_CTRL"),
		new NamedAddress(0x78da, "TIMER_D_PRELOAD"),
		new NamedAddress(0x78dc, "TIMER_D_COUNT"),
		new NamedAddress(0x78f0, "DAC_A_CTRL"),
		new NamedAddress(0x78f1, "DAC_A_DATA"),
		new NamedAddress(0x78f2, "DAC_A_FIFO"),
		new NamedAddress(0x78f8, "DAC_B_CTRL"),
		new NamedAddress(0x78f9, "DAC_B_DATA"),
		new NamedAddress(0x78fa, "DAC_B_FIFO"),
		new NamedAddress(0x78fd, "DAC_CTRL"),
		new NamedAddress(0x78fe, "HEADPHONE_AMP_CTRL"),
		new NamedAddress(0x78ff, "AUDIO_CTRL"),
		new NamedAddress(0x7934, "RTC_SCHEDULER_CTRL"),
		new NamedAddress(0x7935, "RTC_IRQ_STATUS"),
		new NamedAddress(0x7936, "RTC_IRQ_CTRL"),
		new NamedAddress(0x7940, "SPI_CTRL"),
		new NamedAddress(0x7941, "SPI_TX_STATUS"),
		new NamedAddress(0x7942, "SPI_TX_DATA"),
		new NamedAddress(0x7943, "SPI_STATUS"),
		new NamedAddress(0x7944, "SPI_RX_DATA"),
		new NamedAddress(0x7945, "SPI_MISC_STATUS"),
		new NamedAddress(0x7960, "MADC_SETUP"),
		new NamedAddress(0x7961, "MADC_CTRL"),
		new NamedAddress(0x7962, "MADC_DATA"),

		// USB and four-channel system DMA.
		new NamedAddress(0x7a30, "USB_ENABLE"),
		new NamedAddress(0x7a3a, "USB_IRQ_STATUS"),
		new NamedAddress(0x7a80, "DMA0_CTRL"),
		new NamedAddress(0x7a81, "DMA0_SOURCE_LOW"),
		new NamedAddress(0x7a82, "DMA0_DEST_LOW"),
		new NamedAddress(0x7a83, "DMA0_COUNT_LOW"),
		new NamedAddress(0x7a84, "DMA0_SOURCE_HIGH"),
		new NamedAddress(0x7a85, "DMA0_DEST_HIGH"),
		new NamedAddress(0x7a86, "DMA0_COUNT_HIGH"),
		new NamedAddress(0x7a88, "DMA1_CTRL"),
		new NamedAddress(0x7a89, "DMA1_SOURCE_LOW"),
		new NamedAddress(0x7a8a, "DMA1_DEST_LOW"),
		new NamedAddress(0x7a8b, "DMA1_COUNT_LOW"),
		new NamedAddress(0x7a8c, "DMA1_SOURCE_HIGH"),
		new NamedAddress(0x7a8d, "DMA1_DEST_HIGH"),
		new NamedAddress(0x7a8e, "DMA1_COUNT_HIGH"),
		new NamedAddress(0x7a90, "DMA2_CTRL"),
		new NamedAddress(0x7a91, "DMA2_SOURCE_LOW"),
		new NamedAddress(0x7a92, "DMA2_DEST_LOW"),
		new NamedAddress(0x7a93, "DMA2_COUNT_LOW"),
		new NamedAddress(0x7a94, "DMA2_SOURCE_HIGH"),
		new NamedAddress(0x7a95, "DMA2_DEST_HIGH"),
		new NamedAddress(0x7a96, "DMA2_COUNT_HIGH"),
		new NamedAddress(0x7a98, "DMA3_CTRL"),
		new NamedAddress(0x7a99, "DMA3_SOURCE_LOW"),
		new NamedAddress(0x7a9a, "DMA3_DEST_LOW"),
		new NamedAddress(0x7a9b, "DMA3_COUNT_LOW"),
		new NamedAddress(0x7a9c, "DMA3_SOURCE_HIGH"),
		new NamedAddress(0x7a9d, "DMA3_DEST_HIGH"),
		new NamedAddress(0x7a9e, "DMA3_COUNT_HIGH"),
		new NamedAddress(0x7abf, "DMA_COMPLETION_STATUS"),
		new NamedAddress(0x7b80, "SPU_REGISTERS"),
		new NamedAddress(0x7c00, "SOUND_RAM")
	};

	private static final NamedAddress[] VECTOR_ADDRESSES = {
		new NamedAddress(0x00fff5, "VECTOR_SOFTWARE_BREAK"),
		new NamedAddress(0x00fff7, "VECTOR_RESET"),
		new NamedAddress(0x00fff9, "VECTOR_IRQ1_MADC"),
		new NamedAddress(0x00fffb, "VECTOR_IRQ3_DMA"),
		new NamedAddress(0x00fffc, "VECTOR_IRQ4_TIMERS"),
		new NamedAddress(0x00fffd, "VECTOR_IRQ5_VIDEO"),
		new NamedAddress(0x00fffe, "VECTOR_IRQ6_TIMEBASE_RTC")
	};

	@Override
	public String getName() {
		return LOADER_NAME;
	}

	@Override
	public Collection<LoadSpec> findSupportedLoadSpecs(ByteProvider provider) throws IOException {
		List<LoadSpec> specs = new ArrayList<>();
		Header header = readAndValidateHeader(provider);
		if (header != null) {
			specs.add(new LoadSpec(this, header.runtimeBase() * 2,
				new ghidra.program.model.lang.LanguageCompilerSpecPair(
					"unsp:LE:16:default", "default"),
				true));
		}
		return specs;
	}

	@Override
	protected void load(Program program, ImporterSettings settings)
			throws CancelledException, IOException {
		ByteProvider provider = settings.provider();
		Header header = readAndValidateHeader(provider);
		if (header == null) {
			throw new IOException("Invalid or unsupported bM_gbMQa container");
		}

		AddressSpace space = program.getAddressFactory().getDefaultAddressSpace();
		if (space.getAddressableUnitSize() != 2) {
			throw new IOException("MobiGo MBA/GAM files require a 16-bit word-addressed language");
		}

		Address headerAddress = space.getAddress(header.runtimeBase(), true);
		Address loadAddress = space.getAddress(header.loadAddress(), true);
		Address entryAddress = space.getAddress(header.entry(), true);

		FileBytes fileBytes =
			MemoryBlockUtils.createFileBytes(program, provider, settings.monitor());
		try {
			MemoryBlockUtils.createInitializedBlock(program, false, ".mba_header",
				headerAddress, fileBytes, 0, HEADER_SIZE,
				"MBA metadata, 64x104 menu art, and launcher footer", "MBA/GAM",
				true, false, false, settings.log());
			MemoryBlockUtils.createInitializedBlock(program, false, ".mba_body",
				loadAddress, fileBytes, HEADER_SIZE, provider.length() - HEADER_SIZE,
				"Candidate linear file image; entry/code mapping verified, later resources may be transformed",
				"MBA/GAM",
				true, true, true, settings.log());
			program.setImageBase(headerAddress, true);
			markupHeader(program, headerAddress, entryAddress, header);
			createDocumentedHardwareMap(program, space, settings);
			writeProgramInformation(program, header);
		}
		catch (Exception e) {
			throw new IOException("MBA/GAM markup failed", e);
		}

		settings.log().appendMsg(String.format(
			"Loaded %s: base=%#x load=%#x entry=%#x (file offset %#x), header CRC %s",
			header.title(), header.runtimeBase(), header.loadAddress(), header.entry(),
			header.entryFileOffset(),
			header.storedCrc() == header.calculatedCrc() ? "valid" : "INVALID"));
	}

	private Header readAndValidateHeader(ByteProvider provider) throws IOException {
		if (provider.length() < HEADER_SIZE || (provider.length() & 1) != 0) {
			return null;
		}

		BinaryReader reader = new BinaryReader(provider, true);
		if (!Arrays.equals(reader.readByteArray(0, MAGIC.length), MAGIC)) {
			return null;
		}

		long fileWords = reader.readUnsignedInt(0x08);
		long declaredBytes = fileWords * 2;
		long loadAddress = reader.readUnsignedInt(0x18);
		long entry = reader.readUnsignedInt(0x14);
		if (declaredBytes != provider.length() || loadAddress < HEADER_WORDS) {
			return null;
		}

		long runtimeBase = loadAddress - HEADER_WORDS;
		if (runtimeBase >= ADDRESS_SPACE_WORDS || fileWords == 0 ||
			fileWords > ADDRESS_SPACE_WORDS - runtimeBase) {
			return null;
		}

		long runtimeEndExclusive = runtimeBase + fileWords;
		if (entry < loadAddress || entry >= runtimeEndExclusive) {
			return null;
		}

		int storedCrc = reader.readUnsignedShort(0x3c);
		int calculatedCrc = calculateHeaderCrc(reader.readByteArray(0, 0x3c));
		String title = decodeTitle(reader.readByteArray(0x80, 0x20));
		return new Header(fileWords, reader.readUnsignedInt(0x0c),
			reader.readUnsignedInt(0x10), entry, loadAddress,
			reader.readUnsignedInt(0x1c), reader.readUnsignedInt(0x20),
			reader.readUnsignedInt(0x24), reader.readUnsignedInt(0x28),
			storedCrc, calculatedCrc, title);
	}

	private static int calculateHeaderCrc(byte[] bytes) {
		int crc = 0xffff;
		for (byte value : bytes) {
			crc ^= Byte.toUnsignedInt(value) << 8;
			for (int bit = 0; bit < 8; ++bit) {
				crc = (crc & 0x8000) != 0 ? ((crc << 1) ^ 0x1021) & 0xffff
						: (crc << 1) & 0xffff;
			}
		}
		return crc;
	}

	private static String decodeTitle(byte[] bytes) {
		int length = 0;
		while (length < bytes.length && bytes[length] != 0) {
			++length;
		}
		return new String(bytes, 0, length, StandardCharsets.US_ASCII);
	}

	private void markupHeader(Program program, Address headerAddress, Address entryAddress,
			Header header) throws Exception {
		DataType bytes8 = new ArrayDataType(ByteDataType.dataType, 8, 1);
		DataType bytes64 = new ArrayDataType(ByteDataType.dataType, 0x40, 1);
		StructureDataType type = new StructureDataType("mba_header", 0);
		type.add(bytes8, "magic", "ASCII bM_gbMQa");
		type.add(DWordDataType.dataType, "file_size_words",
			"Complete file size in 16-bit words");
		type.add(DWordDataType.dataType, "field_0c", "Unknown");
		type.add(DWordDataType.dataType, "field_10",
			"Unknown; sample-dependent ID/callback-like value");
		type.add(DWordDataType.dataType, "entry_word_address",
			"Verified 22-bit unSP handoff address");
		type.add(DWordDataType.dataType, "body_load_word_address",
			"Runtime word address corresponding to file offset 0x1000");
		type.add(DWordDataType.dataType, "field_1c", "Unknown loader parameter");
		type.add(DWordDataType.dataType, "field_20", "Unknown loader parameter");
		type.add(DWordDataType.dataType, "field_24", "Unknown loader parameter");
		type.add(DWordDataType.dataType, "field_28", "Unknown loader parameter");
		type.add(DWordDataType.dataType, "reserved_2c", null);
		type.add(DWordDataType.dataType, "reserved_30", null);
		type.add(DWordDataType.dataType, "reserved_34", null);
		type.add(DWordDataType.dataType, "reserved_38", null);
		type.add(UnsignedShortDataType.dataType, "header_crc16_ccitt",
			"CRC-16/CCITT over file offsets 0x00..0x3b");
		type.add(UnsignedShortDataType.dataType, "reserved_3e", null);
		type.add(bytes64, "variant_data_40", "Unknown/variant-specific header data");

		DataUtilities.createData(program, headerAddress, type, -1,
			DataUtilities.ClearDataMode.CHECK_FOR_SPACE);

		Address titleAddress = headerAddress.add(0x80);
		DataUtilities.createData(program, titleAddress,
			new ArrayDataType(ByteDataType.dataType, 0x20, 1), -1,
			DataUtilities.ClearDataMode.CHECK_FOR_SPACE);
		program.getSymbolTable().createLabel(titleAddress, "mba_title", SourceType.IMPORTED);
		program.getListing().setComment(titleAddress, CommentType.PLATE,
			"32-byte NUL-padded ASCII title/role: \"" + header.title() + "\"");

		Address paletteAddress = headerAddress.add(0xa0);
		DataUtilities.createData(program, paletteAddress,
			new ArrayDataType(UnsignedShortDataType.dataType, 16, 2), -1,
			DataUtilities.ClearDataMode.CHECK_FOR_SPACE);
		program.getSymbolTable().createLabel(paletteAddress, "mba_menu_palette",
			SourceType.IMPORTED);
		program.getListing().setComment(paletteAddress, CommentType.PLATE,
			"16-entry RGB555 menu palette; bit 15 is transparency");

		Address tileAddress = headerAddress.add(MENU_ART_OFFSET);
		DataUtilities.createData(program, tileAddress,
			new ArrayDataType(ByteDataType.dataType, MENU_ART_SIZE, 1), -1,
			DataUtilities.ClearDataMode.CHECK_FOR_SPACE);
		program.getSymbolTable().createLabel(tileAddress, "mba_menu_art_64x104_4bpp",
			SourceType.IMPORTED);
		program.getListing().setComment(tileAddress, CommentType.PLATE,
			"64x104 indexed visible menu art, 4 bits/pixel, high nibble first");

		Address footerAddress = headerAddress.add(LAUNCHER_FOOTER_OFFSET);
		DataUtilities.createData(program, footerAddress,
			new ArrayDataType(ByteDataType.dataType,
				HEADER_SIZE - LAUNCHER_FOOTER_OFFSET, 1), -1,
			DataUtilities.ClearDataMode.CHECK_FOR_SPACE);
		program.getSymbolTable().createLabel(footerAddress, "mba_launcher_footer",
			SourceType.IMPORTED);
		program.getListing().setComment(footerAddress, CommentType.PLATE,
			"Profile-specific launcher resource footer; required by MobiGo 2 bundle/SY loading");

		SymbolTable symbols = program.getSymbolTable();
		symbols.createLabel(headerAddress, "mba_header", SourceType.IMPORTED);
		symbols.createLabel(entryAddress, "mba_entry", SourceType.IMPORTED);
		symbols.addExternalEntryPoint(entryAddress);
		program.getListing().setComment(entryAddress, CommentType.PLATE,
			String.format("MBA application handoff; file offset %#x",
				header.entryFileOffset()));
	}

	private void createDocumentedHardwareMap(Program program, AddressSpace space,
			ImporterSettings settings) throws Exception {
		Memory memory = program.getMemory();
		Address mmioStart = space.getAddress(0x7000, true);
		if (memory.getBlock(mmioStart) == null) {
			MemoryBlockUtils.createUninitializedBlock(program, false, ".mobigo_mmio",
				mmioStart, 0x2000, "GPL16250/MobiGo 2 MMIO and video/sound RAM",
				"MobiGo 2 homebrew documentation", true, true, false, settings.log());
		}

		Address vectorStart = space.getAddress(0x00fff5, true);
		if (memory.getBlock(vectorStart) == null) {
			MemoryBlockUtils.createUninitializedBlock(program, false, ".unsp_vectors",
				vectorStart, (0x10000 - 0xfff5) * 2L, "unSP segment-zero vectors",
				"MobiGo 2 homebrew documentation", true, true, false, settings.log());
		}

		for (NamedAddress item : DOCUMENTED_ADDRESSES) {
			createDocumentedWord(program, space.getAddress(item.address(), true), item.name());
		}
		for (NamedAddress item : VECTOR_ADDRESSES) {
			createDocumentedWord(program, space.getAddress(item.address(), true), item.name());
		}
	}

	private static void createDocumentedWord(Program program, Address address, String name)
			throws Exception {
		if (program.getListing().getDefinedDataAt(address) == null) {
			DataUtilities.createData(program, address, UnsignedShortDataType.dataType, -1,
				DataUtilities.ClearDataMode.CHECK_FOR_SPACE);
		}
		if (program.getSymbolTable().getPrimarySymbol(address) == null) {
			program.getSymbolTable().createLabel(address, name, SourceType.IMPORTED);
		}
	}

	private static void writeProgramInformation(Program program, Header header) {
		var options = program.getOptions(Program.PROGRAM_INFO);
		options.setString("MBA Format", "bM_gbMQa");
		options.setString("MBA Title/Role", header.title());
		options.setString("MBA File Size (words)", String.format("%#x", header.fileWords()));
		options.setString("MBA Runtime Base", String.format("%#x", header.runtimeBase()));
		options.setString("MBA Body Load Address",
			String.format("%#x", header.loadAddress()));
		options.setString("MBA Entry Address", String.format("%#x", header.entry()));
		options.setString("MBA Entry File Offset",
			String.format("%#x", header.entryFileOffset()));
		options.setString("MBA Runtime End", String.format("%#x", header.runtimeEnd()));
		options.setString("MBA Header CRC",
			String.format("stored=%#06x calculated=%#06x (%s)",
				header.storedCrc(), header.calculatedCrc(),
				header.storedCrc() == header.calculatedCrc() ? "valid" : "INVALID"));
		options.setString("MBA Field 0x0c", String.format("%#x", header.field0c()));
		options.setString("MBA Field 0x10", String.format("%#x", header.field10()));
		options.setString("MBA Field 0x1c", String.format("%#x", header.field1c()));
		options.setString("MBA Field 0x20", String.format("%#x", header.field20()));
		options.setString("MBA Field 0x24", String.format("%#x", header.field24()));
		options.setString("MBA Field 0x28", String.format("%#x", header.field28()));
	}
}
