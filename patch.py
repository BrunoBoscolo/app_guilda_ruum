import re

with open("app/src/main/python/guilda_manager/templates/guilda_manager/upgrades.html", "r") as f:
    content = f.read()

# 1. We will extract the logic inside `renderLines` that creates a single chain into a reusable `createSingleChain(parentId, childId)` function.
# 2. `renderLines` will then just loop through the nodes and call `createSingleChain`.
# 3. `playUpgradeAnimation` will avoid calling `renderLines()`. It will just call `createSingleChain(parentId, childId)` to spawn the new golden chain.

create_chain_func = """
        const chainLinkGeo = new THREE.TorusGeometry(5, 1.5, 8, 16);
        chainLinkGeo.scale(1, 1.5, 1);
        const matLocked = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const matAvailable = new THREE.MeshStandardMaterial({ color: 0x8B1E1E, emissive: 0x8B1E1E, emissiveIntensity: 0.5 });
        const matAcquired = new THREE.MeshStandardMaterial({ color: 0xD4AF37, emissive: 0xD4AF37, emissiveIntensity: 0.8 });

        function createSingleChain(parentId, childId) {
            const parent = nodes[parentId];
            const child = nodes[childId];

            const startX = parent.x;
            const startY = parent.y;
            const endX = child.x;
            const endY = child.y;

            const cp1Y = startY + (endY - startY) / 2;
            const cp2Y = startY + (endY - startY) / 2;

            let material = matLocked;
            let state = 'locked';
            if (child.acquired) {
                material = matAcquired;
                state = 'acquired';
            } else if (parent.acquired) {
                material = matAvailable;
                state = 'available';
            }

            const curve = new THREE.CubicBezierCurve3(
                new THREE.Vector3(startX, startY, 0),
                new THREE.Vector3(startX, cp1Y, 0),
                new THREE.Vector3(endX, cp2Y, 0),
                new THREE.Vector3(endX, endY, 0)
            );

            const chainLength = curve.getLength();
            const numLinks = Math.floor(chainLength / 8);

            const instancedMesh = new THREE.InstancedMesh(chainLinkGeo, material.clone(), numLinks);
            instancedMesh.userData = { state: state, baseIntensity: material.emissiveIntensity, timeOffset: Math.random() * Math.PI * 2 };

            const dummy = new THREE.Object3D();
            const point = new THREE.Vector3();
            const tangent = new THREE.Vector3();
            const up = new THREE.Vector3(0, 1, 0);

            for (let i = 0; i < numLinks; i++) {
                const t = i / (numLinks - 1);
                curve.getPoint(t, point);
                curve.getTangent(t, tangent);

                dummy.position.copy(point);
                dummy.quaternion.setFromUnitVectors(up, tangent);

                if (i % 2 === 0) {
                    dummy.rotateOnAxis(up, Math.PI / 2);
                }

                dummy.updateMatrix();
                instancedMesh.setMatrixAt(i, dummy.matrix);
            }

            instancedMesh.instanceMatrix.needsUpdate = true;
            scene.add(instancedMesh);

            const linkSpacing = chainLength / (numLinks - 1);
            const slack = 1.1;
            const restingDistance = linkSpacing * slack;

            let links = [];
            for (let i = 0; i < numLinks; i++) {
                const t = i / (numLinks - 1);
                curve.getPoint(t, point);
                point.y += Math.sin(t * Math.PI) * 10.0;
                links.push({
                    pos: point.clone(),
                    oldPos: point.clone(),
                    isPinned: (i === 0 || i === numLinks - 1),
                    anchor: point.clone()
                });
            }

            chainMeshes.push({
                parentId: parentId,
                childId: childId,
                mesh: instancedMesh,
                links: links,
                numLinks: numLinks,
                restingDistance: restingDistance
            });

            return chainMeshes[chainMeshes.length - 1];
        }

        function renderLines() {
            chainMeshes.forEach(c => {
                if (c && c.mesh) scene.remove(c.mesh);
            });
            chainMeshes = [];

            Object.keys(nodes).forEach(parentId => {
                const parent = nodes[parentId];
                if (!parent.children) return;

                parent.children.forEach(childId => {
                    createSingleChain(parentId, childId);
                });
            });
        }
"""

# Replace the old renderLines block with the new one.
# It starts around line 410 with `function renderLines() {`
# and ends around line 515 with `});\n            });\n        }`
old_render_lines_regex = r"function renderLines\(\) \{.*?\}\);\n\s*\}\);\n\s*\}"
content = re.sub(old_render_lines_regex, create_chain_func.strip(), content, flags=re.DOTALL)

with open("app/src/main/python/guilda_manager/templates/guilda_manager/upgrades.html", "w") as f:
    f.write(content)
