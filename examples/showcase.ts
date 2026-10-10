import { Container, Graphics, Text } from 'pixi.js';

/** Authored technical example, not an image reconstruction. Design size: 960 x 640. */
export function createShowcase(parent: Container) {
  const root = new Container({ label: 'pixi2d.showcase' });
  const nodes = new Map<string, Container>();
  const label = (text: string, x: number, y: number, size: number, fill = 0x173d35) => {
    const node = new Text({ text, style: { fontFamily: 'Arial', fontSize: size, fill } });
    node.position.set(x, y);
    root.addChild(node);
    return node;
  };
  root.addChild(new Graphics().rect(0, 0, 960, 640).fill(0xf5f2e9));
  label('pixi2D', 56, 42, 42);
  label('Independent objects. One native 2D scene.', 58, 98, 20);
  root.addChild(new Graphics().roundRect(40, 152, 880, 390, 16).fill(0xe3efe7));

  const sun = new Graphics().circle(0, 0, 42).fill(0xefbd59);
  sun.position.set(760, 233);
  root.addChild(sun);
  nodes.set('sun', sun);

  const hills = new Graphics()
    .moveTo(40, 457).bezierCurveTo(240, 310, 373, 377, 530, 475)
    .bezierCurveTo(690, 357, 810, 379, 920, 453).lineTo(920, 542).lineTo(40, 542).closePath().fill(0xb1d1bf)
    .moveTo(40, 505).bezierCurveTo(231, 426, 418, 462, 600, 511)
    .bezierCurveTo(742, 451, 848, 473, 920, 492).lineTo(920, 542).lineTo(40, 542).closePath().fill(0x639c83);
  root.addChild(hills);
  nodes.set('hills', hills);

  const clouds = new Container({ label: 'clouds' });
  for (const [x, y, scale] of [[217, 251, 1], [411, 205, 0.68]]) {
    const cloud = new Graphics().roundRect(-57, -8, 114, 32, 16).fill(0xfffef7)
      .circle(-19, -10, 26).fill(0xfffef7).circle(19, -17, 32).fill(0xfffef7);
    cloud.position.set(x, y);
    cloud.scale.set(scale);
    clouds.addChild(cloud);
  }
  root.addChild(clouds);
  nodes.set('clouds', clouds);

  const balloon = new Container({ label: 'balloon' });
  balloon.position.set(631, 310);
  balloon.addChild(new Graphics().ellipse(0, 0, 89, 104).fill(0x247962)
    .ellipse(0, 0, 54, 104).fill(0x66ac88).ellipse(0, 0, 22, 104).fill(0xe9bc62));
  balloon.addChild(new Graphics().moveTo(-27, 99).lineTo(-23, 135)
    .moveTo(27, 99).lineTo(23, 135).stroke({ color: 0x6a4d30, width: 3 })
    .roundRect(-34, 133, 68, 40, 7).fill(0xbc8851)
    .rect(-34, 140, 68, 5).fill(0x8e6239));
  root.addChild(balloon);
  nodes.set('balloon', balloon);
  label('BALLOON', 58, 574, 15);
  label('Move / rotate / hide independently', 58, 597, 18);
  label('Authored Graphics + Text  |  No 3D runtime', 535, 586, 16);

  parent.addChild(root);
  let disposed = false;
  return {
    root,
    nodes,
    setTime(seconds: number) {
      balloon.position.set(631, 310 + Math.sin(seconds * 1.2) * 12);
      balloon.rotation = Math.sin(seconds * 0.7) * 0.035; // Pixi 2D radians.
      clouds.position.x = Math.sin(seconds * 0.3) * 14;
    },
    reset() {
      balloon.position.set(631, 310);
      balloon.rotation = 0;
      balloon.visible = true;
      clouds.position.set(0, 0);
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      root.removeFromParent();
      root.destroy({ children: true });
    },
  };
}
