import CircleArrow from "../../assets/icons/CircleArrow.tsx";

const processProgramText = (text: string) => {
  const lines = text.split("\n").map((line) => line.trim());

  const content: Array<
    | { type: "text"; text: string }
    | { type: "bullets"; text: string; points: string[] }
  > = [];
  let currentGroup: any;

  lines.forEach((line) => {
    const trimmedLine = line.trim();

    if (trimmedLine.startsWith("-") || trimmedLine.startsWith("–")) {
      if (currentGroup) {
        content.push({ type: "bullets", ...currentGroup });
      }
      currentGroup = {
        text: trimmedLine.substring(1).trim(),
        points: [],
      };
    } else if (trimmedLine.startsWith("•")) {
      if (currentGroup) {
        currentGroup.points.push(trimmedLine.substring(1).trim());
      }
    } else {
      if (currentGroup) {
        content.push({ type: "bullets", ...currentGroup });
        currentGroup = null;
      }
      content.push({ type: "text", text: trimmedLine });
    }
  });

  if (currentGroup) {
    content.push({ type: "bullets", ...currentGroup });
  }

  return content;
};

export const renderProgramText = (
  programData: any,
  textClassName: string,
  listClassName: string,
  listItemClassName: string
) => {
  const content = processProgramText(programData);

  let bulletList: { text: string; points: string[] }[] = [];
  const renderContent = [];

  for (let i = 0; i < content.length; i++) {
    const item = content[i];

    if (item.type === "text") {
      if (bulletList.length > 0) {
        renderContent.push(
          <ul className={listClassName} key={`bullets-${i}`}>
            {bulletList.map((bullet, idx) => (
              <li className={listItemClassName} key={idx}>
                <span>
                  <CircleArrow />
                </span>
                <div>
                  {bullet.text}
                  {bullet.points.length > 0 && (
                    <ul>
                      {bullet.points.map((point, pointIdx) => (
                        <li key={pointIdx}>{point}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ul>
        );
        bulletList = [];
      }

      renderContent.push(
        <p key={`text-${i}`} className={textClassName}>
          {item.text}
        </p>
      );
    } else if (item.type === "bullets") {
      bulletList.push(item);
    }
  }

  if (bulletList.length > 0) {
    renderContent.push(
      <ul className={listClassName} key="bullets-end">
        {bulletList.map((bullet, idx) => (
          <li className={listItemClassName} key={idx}>
            <span>
              <CircleArrow />
            </span>
            <div>
              {bullet.text}
              {bullet.points.length > 0 && (
                <ul>
                  {bullet.points.map((point, pointIdx) => (
                    <li key={pointIdx}>{point}</li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ul>
    );
  }

  return renderContent;
};
