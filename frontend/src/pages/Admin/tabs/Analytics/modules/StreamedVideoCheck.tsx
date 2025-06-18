import { useEffect, useState } from "react";

type VideoItem = {
  source: string;
  course_id: number;
  section: string;
  lesson: string;
  video_link: string;
};

const StreamedVideoCheck = () => {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const decoder = new TextDecoder("utf-8");

    const fetchStreamedJSON = async () => {
      try {
        const response = await fetch(
          "https://dent-s.com/api/healthcheckers/videos/check/stream",
          {
            headers: { Accept: "application/json" },
            signal: controller.signal,
          },
        );

        if (!response.body) {
          throw new Error("Streaming not supported.");
        }

        const reader = response.body.getReader();

        let buffer = "";
        let insideArray = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // Обработка начала массива
          if (!insideArray && buffer.includes("[")) {
            insideArray = true;
            buffer = buffer.substring(buffer.indexOf("[") + 1);
          }

          // Пока есть завершённые JSON-объекты, отделённые запятой
          let boundary = buffer.indexOf("},");
          while (boundary !== -1) {
            const jsonStr = buffer.slice(0, boundary + 1).trim();
            try {
              const parsed: VideoItem = JSON.parse(jsonStr);
              setVideos((prev) => [...prev, parsed]);
            } catch (e) {
              console.warn("Не удалось распарсить:", jsonStr);
            }
            buffer = buffer.slice(boundary + 2);
            boundary = buffer.indexOf("},");
          }
        }

        // Парсим последний объект (перед `]`)
        buffer = buffer.replace(/[\]\s]/g, ""); // убрать ]
        if (buffer.trim()) {
          try {
            const last = JSON.parse(buffer);
            setVideos((prev) => [...prev, last]);
          } catch (e) {
            console.warn("Не удалось распарсить последний объект:", buffer);
          }
        }

        setLoading(false);
      } catch (err) {
        console.error("Ошибка потока:", err);
      }
    };

    fetchStreamedJSON();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    console.log(videos);
  }, [videos]);
  return (
    <div>
      {loading && <p>Загрузка...</p>}
      {videos.map((v, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <strong>{v.lesson}</strong> — <em>{v.section}</em> <br />
          <a href={v.video_link} target="_blank" rel="noopener noreferrer">
            Смотреть
          </a>
        </div>
      ))}
    </div>
  );
};

export default StreamedVideoCheck;
