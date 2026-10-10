# pixi2D — img2pixi2d

Plugin OMP độc lập để tái dựng ảnh thành scene PixiJS **2D có thể chỉnh sửa**: Sprite, Graphics, Text, Mesh 2D và parallax. Bao gồm công cụ intake/crop/compare và hướng dẫn phân tách object, occlusion completion, motion review. Không cài hoặc phụ thuộc beta 3D.

Repository **private**: [img2threejs/pixi2d](https://github.com/img2threejs/pixi2d). Cần tài khoản được cấp quyền đọc; `private: true` trong package.json ngăn npm publish, không thay thế quyền riêng tư trên GitHub.

## Cài đặt

Yêu cầu: OMP, Git/GitHub CLI; Python **3.10+** nếu dùng công cụ ảnh. Scene chạy trong project PixiJS v8 hiện có; release đã kiểm chứng là **8.22.0**. Không cần Python để chạy scene đã tích hợp.

Đăng nhập và clone qua HTTPS (không đặt token trong URL):

```sh
gh auth login --hostname github.com --git-protocol https
gh auth setup-git --hostname github.com
mkdir -p "$HOME/.local/share/img2threejs"
gh repo clone img2threejs/pixi2d "$HOME/.local/share/img2threejs/pixi2d"
omp plugin link "$HOME/.local/share/img2threejs/pixi2d"
omp plugin list --json
```

Nếu đã clone ở nơi khác: `omp plugin link /absolute/path/to/pixi2d`.
`link` cài plugin bằng symlink user-scoped; giữ nguyên thư mục clone. Không chạy `npm install` trong repository plugin; dependency Pixi thuộc project host, không thuộc plugin này.

**Mở phiên OMP mới** để nhận skill `img2pixi2d`.

## Sử dụng trong OMP

Từ project PixiJS cần chỉnh sửa, đính kèm ảnh gốc rồi gọi:

```text
/skill:img2pixi2d
Dùng ảnh tôi đính kèm để tạo scene 2D editable trong project hiện tại.
Giữ đúng silhouette, màu và text. Tách từng object cần di chuyển;
không tạo app thứ hai, không tự bịa hidden pixels.
```

Agent dùng ảnh thật, lập ownership/occlusion plan, tạo factory trong host và kiểm tra canvas thực tế. Plugin không tự sinh app hoặc tự chạy reconstruction khi được cài.

## Công cụ ảnh thủ công

Các lệnh dưới dùng macOS/Linux. Thay PROJECT và IMAGE bằng đường dẫn tuyệt đối của project/ảnh thật:

```sh
PLUGIN="$HOME/.local/share/img2threejs/pixi2d"
PROJECT="/absolute/path/to/your-pixi-project"
IMAGE="/absolute/path/to/reference.png"
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/python" -m pip install -r "$PLUGIN/skills/img2pixi2d/requirements.txt"
cd "$PLUGIN/skills/img2pixi2d"
"$PLUGIN/.venv/bin/python" -m forge.cli --help
"$PLUGIN/.venv/bin/python" -m forge.cli intake "$IMAGE" --workspace "$PROJECT/.img2pixi2d"
```

Intake giữ original bytes và tạo working PNG sRGB RGBA bất biến. Đọc kích thước trả về trước khi chọn bbox có pixel nhìn thấy. Ví dụ crop vùng 16×16: đổi tọa độ theo ảnh thật; vùng ngoài ảnh hoặc hoàn toàn transparent không tạo được layer hữu ích.

```sh
"$PLUGIN/.venv/bin/python" -m forge.cli crop \
  --workspace "$PROJECT/.img2pixi2d" --bbox 0 0 16 16 \
  --out layers/observed-region.png
```

Bbox là `X Y WIDTH HEIGHT` trong ảnh gốc. Nếu vùng chứa object lẫn hàng xóm, thêm `--mask masks/part.png` với matte đã cung cấp/được review, relative với workspace. Crop không segment hoặc inpaint. Đặt lại ảnh trim bằng `trimOffset` trong metadata, không dùng mép texture làm pivot mới.

So sánh **capture canvas thật** với working PNG, cùng kích thước artboard; không tự resize:

```sh
"$PLUGIN/.venv/bin/python" -m forge.cli compare \
  --reference "$PROJECT/.img2pixi2d/reference/working.png" \
  --render "$PROJECT/.img2pixi2d/evidence/render.png" \
  --out "$PROJECT/.img2pixi2d/evidence"
```

Dùng `--bbox X Y WIDTH HEIGHT` để kiểm tra vùng quan trọng. Metric RGB/alpha/SSIM chỉ là chẩn đoán; không chứng minh identity, editability hoặc motion đạt yêu cầu. URL ảnh HTTPS cần đồng ý rõ ràng và `intake --allow-network`.

## Cập nhật và kiểm tra

```sh
git -C "$PLUGIN" pull --ff-only
# Mở phiên OMP mới sau khi cập nhật.
"$PLUGIN/.venv/bin/python" tests/test_tools.py --image "$IMAGE" -v
```

Lệnh test chạy từ `skills/img2pixi2d`, dùng một ảnh thật do người dùng cung cấp; repository không mang fixture ảnh. Nếu requirements đổi, cài lại vào cùng venv. `omp plugin uninstall pixi2d` gỡ đăng ký OMP; không dùng nó để xóa artwork của host.

## Phạm vi và tài liệu

- [Skill](skills/img2pixi2d/SKILL.md): workflow cho agent.
- [Reconstruction](skills/img2pixi2d/references/reconstruction.md), [PixiJS](skills/img2pixi2d/references/pixijs.md).
- [Object separation](skills/img2pixi2d/references/object-separation.md), [occlusion completion](skills/img2pixi2d/references/occlusion-completion.md), [review](skills/img2pixi2d/references/review.md).
- Host sở hữu Application, renderer, ticker và shared resources; scene factory chỉ sở hữu nodes/listeners của mình.
- Một ảnh flattened không cung cấp hidden surfaces chính xác. Không công bố inferred matte/completion là artist alpha hoặc dữ liệu quan sát được.
- Real Mesh3D/Sprite3D/Model3D thuộc plugin riêng [pixi3d](https://github.com/img2threejs/pixi3d); native Mesh 2D và layered parallax vẫn ở đây.

Không đưa ảnh người dùng, workspace `.img2pixi2d`, credential, app hoặc dependency build vào repository plugin. Không suy diễn quyền phân phối artwork từ quyền truy cập repository.
