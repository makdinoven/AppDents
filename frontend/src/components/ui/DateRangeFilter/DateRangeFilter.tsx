import s from "./DateRangeFilter.module.scss";

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (val: string) => void;
  onEndDateChange: (val: string) => void;
}

const DateRangeFilter = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: DateRangeFilterProps) => {
  return (
    <>
      <div className={s.input_wrapper}>
        <label htmlFor="start_date">Start date</label>
        <input
          id="start_date"
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className={s.date_input}
          placeholder="Start date"
        />
      </div>
      <div className={s.input_wrapper}>
        <label htmlFor="end_date">End date</label>
        <input
          id="end_date"
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className={s.date_input}
          placeholder="End date"
        />
      </div>
    </>
  );
};

export default DateRangeFilter;
